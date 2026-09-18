import logging
import os
import time
from dotenv import load_dotenv
from src.notifier import TelegramNotifier

load_dotenv('config/credentials.env')

class OrderExecutor:
    def __init__(self, api_instance):
        self.api = api_instance
        self.notifier = TelegramNotifier()
        self.mode = os.getenv('ENVIRONMENT', 'PAPER_TRADING')
        
    def place_order(self, symbol, exchange, qty, side, order_type='MKT', price=0, sl=None, tp=None, is_exit=False):
        """
        Modified to support Smart Limit Orders & Exit Notification Filtering.
        """
        # --- SECURITY AUDIT: INPUT VALIDATION ---
        if qty <= 0:
            error_msg = f"❌ Invalid Quantity: {qty} for {symbol}"
            logging.error(error_msg)
            self.notifier.send_message(error_msg)
            return None

        # Notify Entry (Only if not an exit order)
        import datetime
        import pytz
        ist_time = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%H:%M:%S  %Y-%m-%d')

        if not is_exit:
            action_word = 'BUY' if side == 'B' else 'SELL'
            price_val = round(price, 2) if price > 0 else 0
            
            msg = f"🔔 <b>Trade Alert!</b>\n"
            msg += f"Symbol: {symbol}\n"
            msg += f"{action_word} AT {price_val}\n"
            msg += f"Qty: {qty}\n"
            
            sl_str = f"SL: {round(sl, 2)}" if sl is not None else ""
            tp_str = f"TP: {round(tp, 2)}" if tp is not None else ""
            
            if sl_str and tp_str:
                msg += f"{sl_str}  {tp_str}\n"
            elif sl_str:
                msg += f"{sl_str}\n"
            elif tp_str:
                msg += f"{tp_str}\n"
                
            msg += f"Time: {ist_time}\n"
            msg += f"Mode: {self.mode}"
            self.notifier.send_message(msg)

        if self.mode == 'PAPER_TRADING':
            price = round(price, 2)
            print(f"📝 [PAPER TRADE] {side} | {qty} | {symbol} @ {order_type} {price}")
            logging.info(f"PAPER TRADE: {side} {qty} {symbol} @ {price}")
            return {"stat": "Ok", "norenordno": f"PAPER_{int(time.time())}"}

        try:
            # Place Order
            # For Limit order, ensure price is provided
            if order_type == 'LMT' and price <= 0:
                print("⚠️ Limit Order requires a valid price. Switching to MKT.")
                order_type = 'MKT'
                price = 0

            res = self.api.place_order(
                buy_or_sell=side,
                product_type='I', 
                exchange=exchange,
                tradename=symbol,
                quantity=qty,
                discloseqty=0,
                price_type=order_type,
                price=price, 
                trigger_price=0,
                retention='DAY',
                remarks='AI_Bot_Trade'
            )
            
            if res and res['stat'] == 'Ok':
                logging.info(f"✅ LIVE ORDER PLACED: {side} {symbol} | OrderID: {res['norenordno']}")
                if not is_exit:
                    self.notifier.send_message(f"✅ Order Success: {res['norenordno']}")
                return res
            else:
                error = res['emsg'] if res else 'Unknown'
                logging.error(f"❌ ORDER FAILED: {error}")
                self.notifier.send_message(f"❌ Order Failed: {error}")
                return None
                
        except Exception as e:
            logging.error(f"❌ EXECUTOR ERROR: {e}")
            self.notifier.send_message(f"❌ EXECUTOR ERROR: {e}")
            return None

    def place_smart_order(self, symbol, exchange, qty, side, target_price, sl=None, tp=None, is_exit=False):
        """Places a Limit order and monitors it (Limit Order Chasing Logic Stub)."""
        target_price = round(target_price, 2)
        print(f"🧠 Smart Limit Order: {symbol} @ {target_price}")
        res = self.place_order(symbol, exchange, qty, side, order_type='LMT', price=target_price, sl=sl, tp=tp, is_exit=is_exit)
        
        if res and 'norenordno' in res and self.mode != 'PAPER_TRADING':
            order_id = res['norenordno']
            pass
        return res

    def send_exit_notification(self, symbol, side, entry_price, exit_price, qty, exit_reason='MANUAL', sl_price=None, entry_time=None):
        """
        Sends a structured, rich notification card when a trade position is closed.
        """
        import datetime
        import pytz

        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.datetime.now(ist)
        ist_time = now.strftime('%H:%M:%S  %Y-%m-%d')

        entry_price = float(entry_price) if entry_price else 0.0
        exit_price = float(exit_price) if exit_price else 0.0
        qty = int(qty) if qty else 1

        # Calculate P&L
        orig_side = 'BUY' if side in ['B', 'BUY'] else 'SELL'
        if orig_side == 'BUY':
            pnl_per_unit = exit_price - entry_price
        else:
            pnl_per_unit = entry_price - exit_price

        total_pnl = round(pnl_per_unit * qty, 2)
        pnl_pct = round((pnl_per_unit / entry_price * 100), 2) if entry_price > 0 else 0.0

        # Exit Reason Label Mapping
        reason_map = {
            'TP_HIT': '🎯 Target Hit (TP)',
            'SL_HIT': '🛑 Stop Loss Hit (SL)',
            'TRAILING_SL': '🔄 Trailing SL Hit',
            'AUTO_SQUARE_OFF': '⏰ 3:15 PM Auto Square-off',
            'EMERGENCY_LIMIT': '🚨 Emergency Risk Exit',
            'MANUAL_FORCE_EXIT': '👤 Manual Force Exit',
            'MANUAL': '👤 Manual Exit'
        }
        reason_label = reason_map.get(exit_reason, exit_reason)

        # Header & P&L Card based on outcome
        if total_pnl > 0:
            header = "🏁 <b>TRADE CLOSED (PROFIT)</b> 🎯"
            pnl_str = f"🟢 <b>+₹{total_pnl:,.2f} (+{pnl_pct:.2f}%)</b>"
        elif total_pnl < 0:
            header = "🏁 <b>TRADE CLOSED (LOSS)</b> 🛑"
            pnl_str = f"🔴 <b>-₹{abs(total_pnl):,.2f} ({pnl_pct:.2f}%)</b>"
        else:
            header = "🏁 <b>TRADE CLOSED (BREAKEVEN)</b> ⚖️"
            pnl_str = "⚖️ <b>₹0.00 (0.00%)</b>"

        # Calculate Achieved R:R
        rr_str = None
        if sl_price:
            risk = abs(entry_price - float(sl_price))
            reward = abs(exit_price - entry_price)
            if risk > 0:
                rr_val = round(reward / risk, 2)
                rr_str = f"1:{rr_val}" if total_pnl >= 0 else f"-1:{rr_val}"

        # Holding Duration
        duration_str = None
        if entry_time:
            try:
                diff_sec = 0
                if isinstance(entry_time, str):
                    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%H:%M:%S'):
                        try:
                            dt_entry = datetime.datetime.strptime(entry_time[:19], fmt)
                            dt_now_naive = datetime.datetime.now()
                            diff_sec = int((dt_now_naive - dt_entry).total_seconds())
                            break
                        except ValueError:
                            pass
                elif isinstance(entry_time, (int, float)):
                    diff_sec = int(time.time() - entry_time)
                elif isinstance(entry_time, datetime.datetime):
                    diff_sec = int((datetime.datetime.now(entry_time.tzinfo) - entry_time).total_seconds())

                if diff_sec > 0:
                    hrs = diff_sec // 3600
                    mins = (diff_sec % 3600) // 60
                    secs = diff_sec % 60
                    if hrs > 0:
                        duration_str = f"{hrs}h {mins}m"
                    elif mins > 0:
                        duration_str = f"{mins}m {secs}s"
                    else:
                        duration_str = f"{secs}s"
            except Exception as e:
                logging.debug(f"Could not format duration: {e}")

        # Construct Message
        msg = f"{header}\n\n"
        msg += f"<b>Symbol:</b> {symbol} ({orig_side})\n"
        msg += f"<b>Reason:</b> {reason_label}\n"
        msg += f"----------------------------------------\n"
        msg += f"<b>Entry Price:</b> ₹{entry_price:.2f}\n"
        msg += f"<b>Exit Price:</b> ₹{exit_price:.2f}\n"
        msg += f"<b>Qty:</b> {qty}\n\n"
        msg += f"<b>P&amp;L:</b> {pnl_str}\n"

        if rr_str:
            msg += f"<b>Achieved R:R:</b> {rr_str}\n"
        if duration_str:
            msg += f"<b>Duration:</b> {duration_str}\n"

        msg += f"<b>Exit Time:</b> {ist_time}\n"
        msg += f"<b>Mode:</b> {self.mode}"

        self.notifier.send_message(msg)

    def get_positions(self):
        if self.mode == 'PAPER_TRADING': return []
        return self.api.get_positions()

    def update_trailing_sl(self, current_price, entry_price, side, current_sl):
        # Dynamic Stop Loss Percentage loading
        sl_pct = 0.40  # default fallback
        try:
            import json
            if os.path.exists('config/live_risk.json'):
                with open('config/live_risk.json', 'r') as f:
                    config = json.load(f)
                    sl_pct = float(config.get('sl_pct', 0.40))
        except:
            pass

        # Calculate initial stop loss distance in price points
        sl_distance = entry_price * (sl_pct / 100)

        if side == 'B':
            new_sl = current_price - sl_distance
            if new_sl > current_sl: 
                return round(new_sl, 2)
        else:
            new_sl = current_price + sl_distance
            if new_sl < current_sl: 
                return round(new_sl, 2)
        return current_sl

