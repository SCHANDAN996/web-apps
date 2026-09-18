import time
import pandas as pd
import numpy as np
import logging
import joblib
import os
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.config_manager import AIConfigManager
from config.feature_config import FEATURES, FEATURE_VERSION, select_features
from src.connector import ShoonyaConnector
from src.indicators import TechnicalIndicators
from src.brain import TradingBrain
from src.multi_timeframe_brain import MultiTimeframeBrain, prediction_from_vote
from src.executor import OrderExecutor
from src.risk_manager import RiskManager
from src.notifier import TelegramNotifier
from src.database import TradingDB 
from src.data_engine import ThirstyDataEngine 
from src.utils import is_market_open
from src.learner import ContinuousLearner
from src.agents import MacroAnalyst, SentimentAgent, OptionChainAgent, TheCouncil
from src.brain_dashboard import update_brain_state
from src.performance_tracker import PerformanceTracker
from src.experience_replay import ExperienceReplayBuffer
from src.evolution_engine import SelfEvolutionEngine
from src.model_registry import ModelRegistry
from src.options_resolver import OptionsResolver
from src import decision_stats
import config.settings as settings
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

# Global thread safety lock & dicts
shared_lock = threading.RLock()
lock = shared_lock
LAST_PRICES = {}

# लॉगिंग सेटअप (Logging Setup - IST Timezone)
if not os.path.exists('logs'): os.makedirs('logs')
import pytz
from datetime import datetime

def ist_converter(*args):
    return datetime.now(pytz.timezone('Asia/Kolkata')).timetuple()

logging.Formatter.converter = ist_converter
logging.basicConfig(level=logging.INFO, filename='logs/trading.log', format='%(asctime)s - %(message)s')

# Suppress noisy libraries
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('yfinance').setLevel(logging.WARNING)
logging.getLogger('shoonya').setLevel(logging.WARNING)

def monitor_stock(symbol, api, brain, executor, risk_mgr, notifier, scaler, open_positions, lock):
    """प्रत्येक स्टॉक के लिए अलग थ्रेड में चलने वाला फंक्शन।"""
    print(f"[INFO] Started Monitoring: {symbol}")
    
    # Thread-Local DB Connection
    db = TradingDB()
    startup_timestamp = None
    
    while True:
        try:
            # डैशबोर्ड से लाइव रिस्क सेटिंग्स लोड करना
            try: risk_mgr.load_live_settings()
            except: pass

            # --- Check Market Hours ---
            # Is Market Open? (Mon-Fri 09:15-15:30 IST)
            if not is_market_open():
                # Allow Crypto to Bypass (TODO: Add check for crypto symbol)
                if symbol in settings.CRYPTO_PAIRS or symbol in settings.FOREX_PAIRS:
                    pass # Crypto/Forex runs 24/7 or has different hours
                else:
                    # NSE Symbol -> Sleep
                    print(f"[SLEEP] Market Closed for {symbol}. Sleeping...")
                    time.sleep(600) # Sleep for 10 mins (CPU optimized)
                    continue 

            # --- 1. डेटाबेस से ताज़ा डेटा प्राप्त करना ---
            # Fetch abundant 1-Minute data so we can resample it.
            # vote() only reads the last 2000 bars (the window learner.py
            # trains on); the rest is headroom for the indicator paths below.
            df_1m = db.get_market_data(symbol, '1m', limit=8000)

            if df_1m.empty or len(df_1m) < 200: # Need enough 1m bars to build 5m bars
                 # Went to log_thought only, which writes to the database and
                 # not to stdout -- so journalctl showed nothing while a symbol
                 # sat here. Both, now, throttled per symbol.
                 starve_key = f"_starve_{symbol}"
                 if time.time() - globals().get(starve_key, 0) > 60:
                     globals()[starve_key] = time.time()
                     msg = f"📉 {symbol}: Insufficient 1m Data ({len(df_1m)}/200 candles). Waiting..."
                     print(msg)
                     logging.warning(msg)
                     try: db.log_thought(msg)
                     except: pass
                 time.sleep(60)
                 continue

            # --- Data Staleness Validation ---
            if not df_1m.empty and isinstance(df_1m.index, pd.DatetimeIndex):
                last_candle_time = df_1m.index[-1]
                now_ist = datetime.now(pytz.timezone('Asia/Kolkata'))
                if hasattr(last_candle_time, 'to_pydatetime'):
                    last_dt = last_candle_time.to_pydatetime()
                    if last_dt.tzinfo is None:
                        last_dt = pytz.timezone('Asia/Kolkata').localize(last_dt)
                    diff_mins = (now_ist - last_dt).total_seconds() / 60.0
                    if diff_mins > 10 and is_market_open():
                        print(f"⚠️ [DATA STALE] {symbol} candle data is {diff_mins:.1f} min old (>10 min threshold). Pausing entry.")
                        time.sleep(30)
                        continue

            # इंडिकेटर्स लागू करना (Multi-Timeframe 5m/15m/1h merged)
            df_5m_rich = TechnicalIndicators.apply_multi_timeframe_features(df_1m)

            if df_5m_rich.empty or len(df_5m_rich) < 60:
                # This was a bare sleep-and-retry: no print, no log_thought,
                # no counter. A symbol that lands here stays here, looping
                # every 10 seconds forever, and the only evidence is the
                # absence of its decisions -- which reads exactly like a
                # market with nothing to say.
                #
                # Throttled to one line a minute per symbol: 32 symbols
                # retrying every 10s would otherwise put out 190 lines a
                # minute, and a flooded log hides things just as well as an
                # empty one.
                stall_key = f"_stall_{symbol}"
                last = globals().get(stall_key, 0)
                if time.time() - last > 60:
                    globals()[stall_key] = time.time()
                    msg = (f"[STALL] {symbol}: indicators produced "
                           f"{len(df_5m_rich)} rows from {len(df_1m)} 1m candles, "
                           f"need 60. Waiting for more data.")
                    print(msg)
                    logging.warning(msg)
                    try: db.log_thought(msg)
                    except: pass
                time.sleep(10)
                continue

            # ट्रेंड एनालिसिस (1H Chart - now part of df_5m_rich implicitly, or we can check the merged col)
            trend_1h = "BULLISH" if df_5m_rich.iloc[-1]['close'] > df_5m_rich.iloc[-1].get('1H_EMA_50', 0) else "BEARISH"

            # लाइव डेटा और ADX फिल्टर
            adx_value = df_5m_rich.iloc[-1]['ADX']
            current_price = round(float(df_5m_rich.iloc[-1]['close']), 2)

            # --- 2. ओपन पोजीशंस मैनेज करना (Trailing Stop Loss & Auto Cut) ---
            with lock: # थ्रेड सेफ्टी के लिए लॉक का उपयोग
                LAST_PRICES[symbol] = current_price
                # --- Auto Intraday Square-off (3:15 PM IST) ---
                # `import datetime` used to sit here. Python treats a name
                # imported anywhere in a function as local to the whole
                # function, so it shadowed the module-level
                # `from datetime import datetime` for every line of
                # monitor_stock -- including line 117, which runs first and
                # therefore raised UnboundLocalError on every cycle of every
                # symbol. The handler at the bottom caught it, wrote to
                # logs/trading.log (not stdout, so journalctl showed nothing)
                # and slept 30s. 5312 times. No symbol ever got past it.
                ist_now = datetime.now(pytz.timezone("Asia/Kolkata"))
                if (ist_now.hour, ist_now.minute) >= (15, 15):
                    if symbol in open_positions:
                        pos = open_positions[symbol]
                        exit_sym = pos.get('trade_symbol', symbol)
                        exit_exchange = pos.get('exchange', 'NSE')
                        print(f"[AUTO-EXIT] 3:15 PM reached. Squaring off {exit_sym}...")
                        executor.place_smart_order(
                            exit_sym, exit_exchange, pos['qty'], 
                            'S' if pos['side'] == 'B' else 'B', current_price,
                            is_exit=True
                        )
                        executor.send_exit_notification(
                            symbol=exit_sym,
                            side=pos['side'],
                            entry_price=pos['entry'],
                            exit_price=current_price,
                            qty=pos['qty'],
                            exit_reason='AUTO_SQUARE_OFF',
                            sl_price=pos.get('sl'),
                            entry_time=pos.get('entry_time')
                        )
                        if 'journal_id' in pos:
                            db.update_trade_journal_exit(pos['journal_id'], current_price, 'AUTO_SQUARE_OFF')
                        del open_positions[symbol]
                        continue

                if symbol in open_positions:
                    pos = open_positions[symbol]
                    # ट्रेलिंग स्टॉप-लॉस अपडेट करना
                    old_sl = pos['sl']
                    new_sl = executor.update_trailing_sl(current_price, pos['entry'], pos['side'], old_sl)
                    
                    if new_sl != old_sl:
                        open_positions[symbol]['sl'] = new_sl
                        ist_time = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%H:%M:%S  %Y-%m-%d')
                        exit_sym = pos.get('trade_symbol', symbol)

                        
                        update_msg = (
                            f"🔄 <b>Stop Loss Updated!</b>\n"
                            f"Symbol: {exit_sym}\n"
                            f"Side: {'BUY' if pos['side'] == 'B' else 'SELL'}\n"
                            f"LTP: {current_price}\n"
                            f"Old SL: {old_sl}\n"
                            f"New SL: {new_sl}\n"
                            f"Time: {ist_time}"
                        )
                        notifier.send_message(update_msg)
                        print(f"[TRAILING] Stop Loss updated for {exit_sym}: {old_sl} -> {new_sl}")

                    
                    # चेक करना कि क्या SL हिट हुआ है
                    if (pos['side'] == 'B' and current_price <= new_sl) or \
                       (pos['side'] == 'S' and current_price >= new_sl):
                        exit_sym = pos.get('trade_symbol', symbol)
                        exit_exchange = pos.get('exchange', 'NSE')
                        print(f"[STOP] SL Hit for {exit_sym}")
                        executor.place_smart_order(
                            exit_sym, exit_exchange, pos['qty'], 
                            'S' if pos['side'] == 'B' else 'B', current_price,
                            is_exit=True
                        )
                        exit_reason = 'TRAILING_SL' if new_sl > old_sl else 'SL_HIT'
                        executor.send_exit_notification(
                            symbol=exit_sym,
                            side=pos['side'],
                            entry_price=pos['entry'],
                            exit_price=current_price,
                            qty=pos['qty'],
                            exit_reason=exit_reason,
                            sl_price=pos.get('sl'),
                            entry_time=pos.get('entry_time')
                        )
                        if 'journal_id' in pos:
                            db.update_trade_journal_exit(pos['journal_id'], current_price, exit_reason)
                        del open_positions[symbol]
                        continue
                        
                    # चेक करना कि क्या TP (Take Profit) हिट हुआ है
                    target_hit = False
                    if 'tp' in pos:
                        if (pos['side'] == 'B' and current_price >= pos['tp']) or \
                           (pos['side'] == 'S' and current_price <= pos['tp']):
                            target_hit = True

                    if target_hit:
                        exit_sym = pos.get('trade_symbol', symbol)
                        exit_exchange = pos.get('exchange', 'NSE')
                        print(f"[PROFIT] TP Hit for {exit_sym} at {current_price}")
                        executor.place_smart_order(
                            exit_sym, exit_exchange, pos['qty'], 
                            'S' if pos['side'] == 'B' else 'B', current_price,
                            is_exit=True
                        )
                        executor.send_exit_notification(
                            symbol=exit_sym,
                            side=pos['side'],
                            entry_price=pos['entry'],
                            exit_price=current_price,
                            qty=pos['qty'],
                            exit_reason='TP_HIT',
                            sl_price=pos.get('sl'),
                            entry_time=pos.get('entry_time')
                        )
                        if 'journal_id' in pos:
                            db.update_trade_journal_exit(pos['journal_id'], current_price, 'TP_HIT')
                        del open_positions[symbol]
                        continue

            # --- 3. AI प्रेडिक्शन और सेंटीमेंट फिल्टर ---
            with lock:
                is_open = symbol in open_positions
            
            # यदि कोई पोजीशन ओपन नहीं है
            if not is_open:
                # Startup cooldown to prevent immediate trading on loaded historical signals
                current_time = df_5m_rich.index[-1]
                if startup_timestamp is None:
                    startup_timestamp = current_time
                    print(f"[STARTUP] {symbol} signal monitoring initialized at {current_time}. Next entry allowed on new candle.")
                    time.sleep(15)
                    continue
                    
                if current_time <= startup_timestamp:
                    time.sleep(15)
                    continue
                # Features come from config/feature_config.py and nowhere else.
                # A fourth private copy of the list used to live right here,
                # shadowing the import at the top of this file, spelled in
                # lowercase and paired with a df.columns.lower() that no other
                # caller performed. select_features raises on a mismatch rather
                # than quietly handing over whichever columns happen to match.
                # This block only feeds the single-shot fallback below, which
                # runs when the brain has no vote(). MultiTimeframeBrain always
                # does, and it builds its own feature frame, so this
                # is dead in the current wiring. It is built lazily rather than
                # unconditionally: preparing it up front meant a scaler whose
                # width no longer matched could `continue` past the MTF vote and
                # skip the symbol outright -- no decision, no log, nothing.
                last_60_3d = None
                if not hasattr(brain, 'vote'):
                    try:
                        last_60 = select_features(df_5m_rich).tail(60).values
                    except KeyError as e:
                        logging.error(f"[FEATURES] {symbol}: {e}")
                        print(f"[ERROR] {symbol}: {e}")
                        continue

                    # Handle NaN/Inf
                    last_60 = np.nan_to_num(last_60, nan=0.0, posinf=1.0, neginf=-1.0)

                    # Scaling used to be skipped in silence when the scaler did
                    # not match the data, feeding raw values to a model trained
                    # on scaled ones -- a wrong answer rather than no answer.
                    if scaler is not None:
                        if last_60.shape[1] != scaler.n_features_in_:
                            logging.error(
                                f"[SCALER] {symbol}: scaler expects {scaler.n_features_in_} "
                                f"features, data has {last_60.shape[1]}; skipping symbol "
                                f"rather than predicting on unscaled input")
                            continue
                        last_60 = scaler.transform(last_60)

                    last_60_3d = np.expand_dims(last_60, axis=0)  # (1, 60, features)

                    # Short vectors used to be zero-padded up to the model's
                    # input size. Zeros are a value, not an absence -- the model
                    # reads them as real observations and answers confidently
                    # about columns that were never measured.
                    expected = brain._get_input_size()
                    if last_60_3d.shape[2] != expected:
                        logging.error(
                            f"[BRAIN] {symbol}: model wants {expected} features, "
                            f"pipeline produced {last_60_3d.shape[2]}; skipping")
                        continue

                # Brain voting over the latest four 5-minute bars
                # (see src/multi_timeframe_brain.py for why not timeframes).
                if hasattr(brain, 'vote'):
                    mtf_result = brain.vote(df_1m)
                    mtf_dir = mtf_result.get('direction', 'HOLD')
                    mtf_conf = mtf_result.get('confidence', 0.5)
                    mtf_agree = mtf_result.get('agreement', 0)

                    # mtf_conf is directional (below 0.5 bearish, above bullish).
                    # It used to be inverted here on the SELL branch, which
                    # turned every bearish call into a BUY proposal downstream.
                    prediction = prediction_from_vote(mtf_result)

                    # The model's own reading of the latest bar, before any
                    # agreement rule collapses it to 0.5. The evening summary
                    # reports how close this came to a trade.
                    raw_score = mtf_result.get('votes', {}).get('now', mtf_conf)

                    if prediction != 0.5:
                        print(f"[MTF] {symbol}: {mtf_dir} Signal (Agreement: {mtf_agree}/4, Conf: {mtf_conf:.2f}, Now: {raw_score:.2f})")
                    else:
                        print(f"[MTF] {symbol}: HOLD (Agreement: {mtf_agree}/4, Conf: {mtf_conf:.2f}, Now: {raw_score:.2f})")

                    if mtf_result.get('failed_views'):
                        print(f"[MTF] {symbol}: degraded -- {mtf_result['failed_views']}")
                else:
                    prediction = brain.predict(last_60_3d)
                    raw_score = prediction
                
                # Push to Brain Dashboard (live frontend sync)
                signal = 'BUY' if prediction > 0.75 else ('SELL' if prediction < 0.25 else 'HOLD')
                update_brain_state(symbol, prediction, signal, abs(prediction - 0.5) * 2)
                
                # --- COMPONENT TRACKING (Heavyweight Check) ---
                heavyweight_score = 0
                if symbol in ["NIFTY", "BANKNIFTY"]:
                    # Check Reliance & HDFC Bank Sentiment
                    try:
                        rel_sent = db.get_news_sentiment("RELIANCE")
                        hdfc_sent = db.get_news_sentiment("HDFCBANK")
                        heavyweight_score = (rel_sent + hdfc_sent) / 2
                    except: pass
                
                # न्यूज़ सेंटीमेंट चेक करना
                sentiment_score = db.get_news_sentiment(symbol)
                
                # --- BRAIN v4.0: THE COUNCIL ---
                # 4. Initialize Agents (The Brain's Advisors)
                print("   ... Summoning The Council")
                macro_agent = MacroAnalyst(db)
                sentiment_agent = SentimentAgent(db)
                option_agent = OptionChainAgent(db) # NEW: Smart Money Analyst
                
                # Risk Manager (Capital Protection)
                print("   ... Engaging Risk Protocols")
                # The risk_mgr is passed as an argument to monitor_stock,
                # so we should use the existing instance rather than re-initializing.
                # The instruction to re-initialize risk_mgr here is likely a copy-paste error
                # from a different context where risk_mgr was not passed as an argument.
                # We will keep the existing risk_mgr instance.
                # risk_mgr = risk_manager.RiskManager(db) # Original instruction, commented out for logical consistency
                
                # The Council (Supreme Court)
                print("   ... Assembling The Council")
                council = TheCouncil(macro_agent, sentiment_agent, option_agent, risk_mgr)
                
                # 2. Get Technical Signal (The Specialist)
                # Prediction 0-1. >0.6=Buy, <0.4=Sell
                tech_signal = prediction 
                
                # Persist Technical Agent State (Latest View)
                tech_status = "NEUTRAL"
                if tech_signal > 0.6: tech_status = "BULLISH"
                elif tech_signal < 0.4: tech_status = "BEARISH"
                db.update_agent_state("TECHNICAL", tech_status, tech_signal, f"Symbol: {symbol}")
                
                # 3. Council Review (The Vote)
                # Convert raw prediction (0-1) to confidence (0-1 where 1 = most confident)
                # 0.14 → 0.72 confidence SELL, 0.85 → 0.70 confidence BUY
                actual_confidence = abs(prediction - 0.5) * 2
                action, confidence, reason = council.review_trade(symbol, tech_signal, actual_confidence)

                # Tally for the evening Telegram summary. Never let bookkeeping
                # stop a trading decision.
                try:
                    decision_stats.record(symbol, raw_score, action, confidence, reason)
                except Exception as e:
                    logging.error(f"[STATS] {symbol}: {e}")

                # 4. Log the Decision Process
                thought = f"Council Decision for {symbol}: {action} | Conf: {confidence:.2f} | Reason: {reason}"
                print(f"[THOUGHT] {thought}")
                try: db.log_thought(thought)
                except: pass
                
                if action and confidence >= 0.60:
                    if action == 'BUY':
                         print(f"[INFO] 🟢 Bullish Signal {symbol} (Conf: {confidence:.2f}) | {reason}")
                    else:
                         print(f"[INFO] 🔴 Bearish Signal {symbol} (Conf: {confidence:.2f}) | {reason}")
                else:
                    print(f"[INFO] ⏸️ No Trade / Vetoed for {symbol} (Conf: {confidence:.2f}) | {reason}")
                    continue

                # --- ट्रेडिंग गेट ---
                # बंद है क्योंकि मौजूदा मॉडल हर चीज़ SELL करता है। उसे जो लेबल
                # सिखाए गए वे दिशा बताते ही नहीं थे — data_loader.py BUY और SELL
                # दोनों सही सेटअपों को एक ही लेबल 1 देता है — और 1482 नमूनों में
                # सिर्फ़ 17 पॉज़िटिव थे (1.1%), जिनमें एक भी BUY नहीं। इतने
                # असंतुलित लक्ष्य पर मॉडल ने "जवाब हमेशा 0 है" सीख लिया, जो नीचे
                # 4/4 सहमति वाले SELL की तरह दिखता है।
                #
                # निर्णय अब भी असली हैं और लॉग होते हैं — सिर्फ़ ऑर्डर नहीं जाता।
                # 3-class (BUY/SELL/NO-TRADE) पर दोबारा ट्रेन करने के बाद
                # credentials.env में TRADING_ENABLED=true कर दें।
                if os.getenv('TRADING_ENABLED', 'false').lower() not in ('1', 'true', 'yes'):
                    msg = (f"[GATE] {symbol}: {action} @ conf {confidence:.2f} "
                           f"रोका गया — TRADING_ENABLED बंद है (मॉडल दोबारा ट्रेन होना बाक़ी)")
                    print(msg)
                    try: db.log_thought(msg)
                    except: pass
                    continue

                # ट्रेड एग्जीक्यूट करना
                if action and confidence >= 0.60:
                    action_code = 'B' if action == 'BUY' else 'S'
                    with lock:
                        # 1. Calculate Quantity Dynamic
                        try:
                            trade_confidence = confidence if 'confidence' in locals() else prediction
                            
                            atr_value = 0
                            if 'ATR_14' in df_5m_rich.columns:
                                atr_value = df_5m_rich.iloc[-1]['ATR_14']
                            elif 'ATR' in df_5m_rich.columns:
                                atr_value = df_5m_rich.iloc[-1]['ATR']
                            
                            qty = risk_mgr.calculate_position_size(symbol, current_price, trade_confidence, atr_value=atr_value)
                        except Exception as e:
                            print(f"[ERROR] Qty Calc Failed: {e}")
                            qty = 0

                        if qty > 0 and risk_mgr.can_place_trade():
                            trade_symbol = symbol
                            trade_exchange = 'NSE'
                            trade_instrument = 'EQ'
                            trade_qty = qty
                            trade_price = current_price
                            
                            enable_options = getattr(settings, 'ENABLE_OPTIONS_TRADING', False)
                            if symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
                                if not enable_options:
                                    print(f"🚫 [OPTIONS] Options trading is DISABLED in config. Skipping option trade for {symbol}.")
                                    continue
                                try:
                                    opt_resolver = OptionsResolver(db)
                                    opt_info = opt_resolver.resolve_option_symbol(
                                        symbol, current_price, 
                                        'BUY' if action_code == 'B' else 'SELL'
                                    )
                                    trade_symbol = opt_info['trading_symbol']
                                    trade_exchange = opt_info['exchange']  # NFO
                                    trade_instrument = opt_info['instrument']  # CE or PE
                                    trade_qty = opt_info['lot_size']
                                    # For options, we always BUY the CE/PE
                                    action_code = 'B'
                                    print(f"[OPTIONS] {symbol} → {trade_symbol} ({trade_instrument}) Lot: {trade_qty}")
                                except Exception as e:
                                    print(f"[OPTIONS] Resolver failed: {e}")
                                    continue
                            
                            # Calculate SL and TP before order placement to include in Telegram alert
                            sl, tp = risk_mgr.calculate_stop_loss(trade_price, action_code)

                            print(f"[SIGNAL] Executing Trade: {trade_symbol} {action_code} | Qty: {trade_qty} | Price: {trade_price}")
                            res = executor.place_smart_order(trade_symbol, trade_exchange, trade_qty, action_code, trade_price, sl=sl, tp=tp)
                            
                            if res:
                                # Log to Trade Journal
                                trade_mode = 'PAPER' if executor.mode == 'PAPER_TRADING' else 'LIVE'
                                journal_id = db.log_trade_journal(
                                    trade_type=trade_mode,
                                    symbol=trade_symbol,
                                    instrument=trade_instrument,
                                    side='BUY' if action_code == 'B' else 'SELL',
                                    qty=trade_qty,
                                    entry_price=trade_price,
                                    sl_price=sl,
                                    tp_price=tp,
                                    confidence=confidence,
                                    council_reason=reason,
                                    planned_rr=settings.RISK_REWARD_RATIO
                                )
                                
                                open_positions[symbol] = {
                                    'side': action_code, 'entry': trade_price,
                                    'sl': sl, 'tp': tp, 'qty': trade_qty,
                                    'journal_id': journal_id,
                                    'trade_symbol': trade_symbol,
                                    'exchange': trade_exchange,
                                    'entry_time': datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')
                                }
                                risk_mgr.increment_trade_count()
                                
                                # Log trade
                                order_id = res.get('norenordno', 'NA')
                                db.log_trade(trade_symbol, action_code, trade_price, trade_qty, order_id)
                                
                                # Log Thought
                                try: db.log_thought(f"Executed {action_code} {trade_symbol} ({trade_instrument}). Qty: {trade_qty}. SL: {sl}. TP: {tp}. R:R: {settings.RISK_REWARD_RATIO}")
                                except: pass

                        elif qty == 0:
                            print(f"[RISK] Trade Skipped for {symbol}: Calculated Qty is 0 (Low confidence or capital limit)")
                        else:
                            print(f"[RISK] Trade Blocked by Manager: {symbol}")
                            try: db.log_thought(f"🛑 Risk Manager Blocked Trade for {symbol}. Check Limits.")
                            except: pass

            time.sleep(15) # Scan interval (CPU optimized from 5s)
            
        except Exception as e:
            # This went to logging.error alone, which writes to
            # logs/trading.log and never to stdout -- so journalctl showed a
            # bot that had simply gone quiet. An UnboundLocalError hid here for
            # weeks: every symbol raised on every cycle, slept 30s, and tried
            # again, and the only outward sign was the absence of decisions.
            #
            # Now it prints too, with the exception type and a per-symbol
            # count, so a permanently failing symbol is visible as one.
            err_key = f"_err_{symbol}"
            count = globals().get(err_key, 0) + 1
            globals()[err_key] = count
            msg = f"[ERROR] monitoring {symbol}: {type(e).__name__}: {e} (failure #{count})"
            logging.error(msg, exc_info=(count == 1))
            if count <= 3 or count % 20 == 0:
                print(msg)
            time.sleep(30)

def check_manual_orders(executor):
    """
    Background thread to check for manual trade requests from UI.
    Reads config/trade_requests.json, executes, and clears processed.
    """
    db = TradingDB()
    REQ_FILE = 'config/trade_requests.json'
    print("[INFO] Manual Trade Listener Started...")
    
    while True:
        try:
            if os.path.exists(REQ_FILE):
                reqs = []
                try:
                    with open(REQ_FILE, 'r') as f:
                        content = f.read()
                        if content: reqs = json.loads(content)
                except Exception as e:
                    print(f"Error reading trade requests: {e}")
                
                # Filter Pending Requests
                pending = [r for r in reqs if r.get('status') == 'PENDING']
                
                if pending:
                    # Clear file immediately to prevent double execution (optimistic locking)
                    # or better, write back 'PROCESSING' status. 
                    # For simplicity, we process and empty the list from file.
                    with open(REQ_FILE, 'w') as f:
                        json.dump([], f) 
                        
                    for req in pending:
                        print(f"🚀 [MANUAL TRADE] Executing {req['side']} {req['symbol']}...")
                        
                        res = executor.place_order(
                            symbol=req['symbol'],
                            exchange='NSE', # Default to NSE for now
                            qty=req['qty'],
                            side=req['side'],
                            order_type=req['type'],
                            price=req['price']
                        )
                        
                        status = "COMPLETED" if res else "FAILED"
                        if res:
                            # Log to DB
                            db.log_trade(req['symbol'], req['side'], req.get('price', 0), req['qty'], res.get('norenordno', 'MAN_NA'))
                            print(f"✅ Manual Trade Done: {res.get('norenordno')}")
                        else:
                            print(f"❌ Manual Trade Failed")

            time.sleep(1)
        except Exception as e:
            print(f"Manual Trade Listener Error: {e}")
            time.sleep(5)

def db_maintenance(db):
    """
    Background thread to auto-prune database every 6 hours 
    and manually checkpoint WAL to prevent storage explosion.
    """
    print("[INFO] Database Maintenance Thread Started...")
    while True:
        try:
            # Sleep 6 hours (21600 seconds)
            time.sleep(21600)
            print("[MAINTENANCE] Running database prune & checkpoint...")
            db.prune_old_data()
            try:
                # PRAGMA wal_checkpoint does not raise when it cannot finish --
                # it returns (busy, log_pages, checkpointed_pages) and leaves it
                # to the caller to look. This printed "OK" unconditionally, so
                # the WAL grew to 14 GB (3.4 million pages) against a 5 GB
                # database while the log said the checkpoint was fine every six
                # hours. The disk reached 87% before anyone noticed.
                busy, log_pages, checkpointed = db.conn.execute(
                    "PRAGMA wal_checkpoint(TRUNCATE);").fetchone()

                wal_mb = log_pages * 4096 / (1024 * 1024)

                if busy:
                    msg = (f"⚠️ WAL checkpoint BLOCKED (busy=1): {log_pages} pages "
                           f"(~{wal_mb:.0f} MB) still in the WAL. A reader is "
                           f"holding an old snapshot, so it cannot be reset.")
                    logging.warning(msg)
                    print(msg)
                elif log_pages > 0:
                    msg = (f"⚠️ WAL checkpoint incomplete: {checkpointed} of "
                           f"{log_pages} pages written (~{wal_mb:.0f} MB left). "
                           f"Overlapping readers keep the WAL from resetting.")
                    logging.warning(msg)
                    print(msg)
                else:
                    print(f"✅ WAL checkpoint OK ({checkpointed} pages written, WAL empty).")

                # A WAL this size means checkpointing has been losing for a
                # while. Say so loudly -- it fills the disk quietly otherwise.
                if wal_mb > 500:
                    alert = (f"🚨 WAL is {wal_mb:.0f} MB. Stop the bot and run "
                             f"PRAGMA wal_checkpoint(TRUNCATE) with no readers "
                             f"attached, or the disk will fill.")
                    logging.error(alert)
                    print(alert)
            except Exception as ce:
                logging.error(f"WAL checkpoint error: {ce}")
                print(f"❌ WAL Checkpoint Error: {ce}")
        except Exception as e:
            print(f"Database Maintenance Error: {e}")
            time.sleep(60)

def load_open_positions_from_db(db, trading_symbols):
    """Load open positions from the database on startup."""
    open_positions = {}
    try:
        cursor = db.conn.cursor()
        cursor.execute("SELECT id, symbol, side, qty, entry_price, sl_price, tp_price, instrument, entry_time FROM trade_journal WHERE status = 'OPEN'")
        rows = cursor.fetchall()
        for row in rows:
            journal_id, trade_symbol, side, qty, entry_price, sl_price, tp_price, instrument, entry_time = row
            
            # Find matching base symbol
            base_symbol = None
            for sym in trading_symbols:
                if trade_symbol.startswith(sym):
                    base_symbol = sym
                    break
            
            if base_symbol:
                open_positions[base_symbol] = {
                    'side': 'B' if side == 'BUY' else 'S',
                    'entry': entry_price,
                    'sl': sl_price,
                    'tp': tp_price,
                    'qty': qty,
                    'journal_id': journal_id,
                    'trade_symbol': trade_symbol,
                    'exchange': 'NFO' if instrument in ['CE', 'PE'] else 'NSE',
                    'entry_time': entry_time
                }
                print(f"[RECOVERY] Loaded open position for {base_symbol} ({trade_symbol}): {side} | Qty: {qty} | Entry: {entry_price} | SL: {sl_price} | TP: {tp_price}")
            else:
                print(f"[RECOVERY] [WARN] Could not map trade symbol {trade_symbol} to any trading symbol.")
    except Exception as e:
        print(f"[RECOVERY] [ERROR] Failed to load open positions: {e}")
    return open_positions

def main():
    # सभी मॉड्यूल इनिशियलाइज़ करना
    api = ShoonyaConnector()
    base_brain = TradingBrain()
    brain = MultiTimeframeBrain(base_brain, feature_columns=FEATURES)
    print("[INFO] 🧠 Multi-Timeframe Brain Activated (1m, 5m, 15m, 1H voting)!")
    executor = OrderExecutor(api)
    notifier = TelegramNotifier()
    db = TradingDB()
    
    # One scaler file, the one build_sequences writes after every fit and
    # MultiTimeframeBrain reads at inference. This used to prefer
    # models/scaler.pkl and fall back to scaler_v2.pkl, and scaler.pkl was
    # stale -- 18 features against the contract's 19 -- so main.py and the
    # brain were holding different scalers fitted on different feature lists.
    scaler = None
    if os.path.exists(MultiTimeframeBrain.DEFAULT_SCALER_PATH):
        scaler = joblib.load(MultiTimeframeBrain.DEFAULT_SCALER_PATH)
        width = getattr(scaler, "n_features_in_", None)

        if width == len(FEATURES):
            print(f"[INFO] Loaded scaler ({width} features, matches contract)")
        else:
            # Do not transform with it. A scaler fitted on a different column
            # set maps each feature by the wrong statistics, which is a wrong
            # answer rather than a missing one.
            msg = (f"[SCALER] {MultiTimeframeBrain.DEFAULT_SCALER_PATH} has "
                   f"{width} features, contract has {len(FEATURES)} -- refusing "
                   f"to use it. It will be refitted on the next training run.")
            logging.error(msg)
            print(f"[ERROR] {msg}")
            scaler = None
    else:
        msg = (f"[SCALER] {MultiTimeframeBrain.DEFAULT_SCALER_PATH} not found -- "
               f"it is written by the first training run.")
        logging.warning(msg)
        print(f"[WARN] {msg}")
    
    # Load Unified Configuration
    config = AIConfigManager()
    config.load()
    trading_symbols = config.get('trading.symbols', default=settings.TRADING_SYMBOLS)

    risk_mgr = RiskManager(api, config=config)
    open_positions = load_open_positions_from_db(db, trading_symbols)

    # ब्रोकर लॉगिन
    if not api.login():
        if os.getenv('ENVIRONMENT', 'PAPER_TRADING') == 'PAPER_TRADING':
            print("[WARN] Login Failed. Starting in PAPER_TRADING mode.")
        else:
            return

    notifier.send_message("<b>AI Trading Engine v4.0 (ThreadPool)</b> started successfully!")

    # --- डेटा इंजन शुरू करना (Yahoo Finance — No Shoonya Dependency) ---
    data_engine = ThirstyDataEngine()  # Yahoo Finance based, no API needed
    data_engine.start_drinking()
    print("[INFO] 🚰 Data Engine is now drinking market data (Yahoo Finance)...")

    # One worker per symbol, not a pool of five.
    #
    # monitor_stock never returns -- it is a `while True` that watches its symbol
    # for the life of the process. A pool of 5 therefore handed its 5 workers to
    # the first 5 symbols permanently, and the remaining 27 sat in the queue
    # forever, never monitored, never mentioned. Only NIFTY, BANKNIFTY, FINNIFTY,
    # RELIANCE and HDFCBANK were ever watched.
    #
    # These threads spend nearly all their time in time.sleep(), and the brain
    # and its weights are shared, so the cost of the extra 27 is small.
    print(f"[INFO] ⚡ Spawning one monitor thread per symbol ({len(trading_symbols)} symbols)...")
    pool_executor = ThreadPoolExecutor(max_workers=len(trading_symbols) or 1)
    for symbol in trading_symbols:
        pool_executor.submit(monitor_stock, symbol, api, brain, executor, risk_mgr, notifier, scaler, open_positions, shared_lock)

    # --- Start Manual Trade Listener Thread ---
    t_manual = threading.Thread(target=check_manual_orders, args=(executor,))
    t_manual.daemon = True
    t_manual.start()

    # --- Start DB Maintenance Thread ---
    t_maint = threading.Thread(target=db_maintenance, args=(db,))
    t_maint.daemon = True
    t_maint.start()

    # 6. User Portal (Dashboard Command Listener - Placeholder)
    # TODO: Add socket listener here

    # 7. Continuous Learning Engine (New)
    try:
        print("[INFO] Starting Continuous AI Learner...")
        learner = ContinuousLearner(db, brain)
        learner.start()
    except Exception as e:
        print(f"[WARN] Learner failed to start: {e}")

    # 8. Performance Tracker (V2 — Live Monitoring)
    try:
        perf_tracker = PerformanceTracker(window=200)
        print(f"[INFO] 📊 Performance Tracker initialized.")
    except Exception as e:
        perf_tracker = None
        print(f"[WARN] Performance Tracker failed: {e}")

    # 9. Experience Replay Buffer (V2 — Memory-Based Learning)
    try:
        replay_buffer = ExperienceReplayBuffer(max_size=10000)
        stats = replay_buffer.get_stats()
        print(f"[INFO] 🧠 Experience Replay Buffer: {stats.get('size', 0)} experiences loaded.")
    except Exception as e:
        replay_buffer = None
        print(f"[WARN] Experience Replay failed: {e}")

    # 10. Model Registry (V2 — Version Control)
    try:
        model_registry = ModelRegistry()
        latest = model_registry.get_latest_version()
        if latest:
            print(f"[INFO] 📦 Model Registry: active version {latest['version_id']}")
        else:
            print(f"[INFO] 📦 Model Registry initialized (no versions yet).")
    except Exception as e:
        model_registry = None
        print(f"[WARN] Model Registry failed: {e}")

    # 11. Self-Evolution Engine (V2 — Autonomous Daily Improvement)
    try:
        evolution_engine = SelfEvolutionEngine(brain, db)
        evolution_engine.start()
        print("[INFO] 🧬 Self-Evolution Engine started (runs daily at 4 PM IST).")
    except Exception as e:
        print(f"[WARN] Evolution Engine failed to start: {e}")

    # 12. Daily Telegram report: now sent by cron via daily_summary.py
    # (deploy/tradekaro-daily-summary.cron, 15:45 IST). The in-bot scheduler
    # fired at 16:00 server time -- UTC, so 21:30 IST -- and went silent
    # whenever the bot itself was down, which is exactly when it was needed.
    # Starting both would send two reports a day.

    # --- MAIN LOOP ---
    print("\n[READY] TradeKaro Bot is Armed & Ready!")

    last_pnl_check = 0
    try:
        while True:
            time.sleep(1)
            
            # Check emergency exit every 10 seconds
            now = time.time()
            if now - last_pnl_check >= 10:
                last_pnl_check = now
                try:
                    import datetime
                    import pytz
                    ist = pytz.timezone('Asia/Kolkata')
                    today_str = datetime.datetime.now(ist).strftime('%Y-%m-%d')
                    
                    # 1. Realized PnL from DB
                    cursor = db.conn.cursor()
                    cursor.execute("SELECT SUM(pnl) FROM trade_journal WHERE entry_time >= ?", (f"{today_str} 00:00:00",))
                    row = cursor.fetchone()
                    realized_pnl = float(row[0]) if row and row[0] is not None else 0.0
                    
                    # 2. Unrealized PnL from open positions
                    unrealized_pnl = 0.0
                    with shared_lock:
                        for sym, pos in open_positions.items():
                            cur_price = LAST_PRICES.get(sym, pos['entry'])
                            diff = cur_price - pos['entry']
                            pos_pnl = diff * pos['qty']
                            if pos['side'] == 'S':
                                pos_pnl = -pos_pnl
                            unrealized_pnl += pos_pnl
                    
                    total_pnl = realized_pnl + unrealized_pnl
                    
                    # Check and execute emergency exit
                    if risk_mgr.check_emergency_exit(total_pnl):
                        print(f"[EMERGENCY] Daily Loss Limit Hit: {total_pnl}. Squaring off all positions...")
                        notifier.send_message(f"🚨 <b>[EMERGENCY] Daily Loss Limit Hit!</b>\nDaily P&L: ₹{total_pnl:.2f}\nSquaring off all open positions and halting trading for the day.")
                        
                        with shared_lock:
                            for sym in list(open_positions.keys()):
                                pos = open_positions[sym]
                                cur_price = LAST_PRICES.get(sym, pos['entry'])
                                exit_sym = pos.get('trade_symbol', sym)
                                exit_exchange = pos.get('exchange', 'NSE')
                                
                                # Place square-off order
                                exit_side = 'S' if pos['side'] == 'B' else 'B'
                                executor.place_smart_order(
                                    exit_sym, exit_exchange, pos['qty'], exit_side, cur_price,
                                    is_exit=True
                                )
                                executor.send_exit_notification(
                                    symbol=exit_sym,
                                    side=pos['side'],
                                    entry_price=pos['entry'],
                                    exit_price=cur_price,
                                    qty=pos['qty'],
                                    exit_reason='EMERGENCY_LIMIT',
                                    sl_price=pos.get('sl'),
                                    entry_time=pos.get('entry_time')
                                )
                                
                                # Update DB
                                if 'journal_id' in pos:
                                    db.update_trade_journal_exit(pos['journal_id'], cur_price, 'EMERGENCY_LIMIT')
                                    
                                # Remove from open positions
                                del open_positions[sym]
                except Exception as pnl_err:
                    print(f"[ERROR] Emergency Daily Loss check failed: {pnl_err}")
    except KeyboardInterrupt:
        print("[STOP] Shutting down AI Engine...")

if __name__ == "__main__":
    main()