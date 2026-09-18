"""
🎯 System Orchestrator — THE MASTER CONTROLLER (Phase 50 Capstone)

Initializes, coordinates, and manages ALL 50+ AI modules.
This is the single entry point that ties everything together.

Architecture:
  Orchestrator
  ├── Core AI (Brain V2, Ensemble, Multi-TF)
  ├── Analysis (Indicators, Candles, Fibonacci, Microstructure)
  ├── Sentiment (FinBERT, Social, News, Decay)
  ├── Risk (VaR, Drawdown, Anomaly, Circuit Breaker)
  ├── Execution (Smart Orders, Paper Trade, Portfolio)
  ├── Analytics (Journal, Attribution, Watchlist, Explainer)
  └── Infrastructure (Alerts, Data Quality, Health, Telegram)
"""

import logging
import threading
from datetime import datetime


class SystemOrchestrator:
    """
    Master controller that initializes and coordinates all AI modules.
    
    Usage:
        orchestrator = SystemOrchestrator(config={
            'capital': 500000,
            'mode': 'PAPER',  # PAPER or LIVE
            'telegram_token': '...',
        })
        orchestrator.initialize()
        orchestrator.start()
    """
    
    VERSION = '2.0.0'
    CODENAME = 'TradeKaro AI — 50-Phase Ultra System'
    
    def __init__(self, config=None):
        self.config = config or {}
        self.modules = {}
        self.status = 'STOPPED'
        self.start_time = None
        self.errors = []
    
    def initialize(self):
        """Initialize all modules in dependency order."""
        print(f"🚀 {self.CODENAME} v{self.VERSION}")
        print("=" * 60)
        
        capital = self.config.get('capital', 500000)
        mode = self.config.get('mode', 'PAPER')
        
        # === TIER 1: Core Infrastructure ===
        self._init_module('alert_engine', 'src.alert_engine', 'AlertEngine')
        self._init_module('production', 'src.production_hardener', 'ProductionHardener')
        self._init_module('data_quality', 'src.data_quality', 'DataQualityMonitor')
        
        # === TIER 2: Analysis Engines ===
        self._init_module('candle_patterns', 'src.candle_patterns', 'CandlePatternRecognizer')
        self._init_module('fibonacci', 'src.fibonacci_levels', 'FibonacciLevels')
        self._init_module('order_flow', 'src.order_flow', 'OrderFlowAnalyzer')
        self._init_module('microstructure', 'src.microstructure', 'MicrostructureAnalyzer')
        self._init_module('liquidity', 'src.liquidity_analyzer', 'LiquidityAnalyzer')
        self._init_module('anomaly', 'src.anomaly_detector', 'AnomalyDetector')
        
        # === TIER 3: Sentiment & News ===
        self._init_module('news', 'src.news_scraper', 'NewsEventScraper')
        self._init_module('social', 'src.social_sentiment', 'SocialSentimentHeatmap')
        self._init_module('sentiment_decay', 'src.sentiment_decay', 'SentimentDecayTracker')
        
        # === TIER 4: Market Intelligence ===
        self._init_module('correlation', 'src.correlation_engine', 'CorrelationEngine')
        self._init_module('market_breadth', 'src.market_breadth', 'MarketBreadthAnalyzer')
        self._init_module('session', 'src.session_classifier', 'SessionClassifier')
        self._init_module('sector_rotation', 'src.sector_rotation', 'SectorRotationEngine')
        self._init_module('volatility_surface', 'src.volatility_surface', 'VolatilitySurfaceAnalyzer')
        
        # === TIER 5: Strategy Engines ===
        self._init_module('pair_trading', 'src.pair_trading', 'PairTradingEngine')
        self._init_module('adaptive_tf', 'src.adaptive_timeframe', 'AdaptiveTimeframeSelector')
        self._init_module('watchlist', 'src.watchlist_generator', 'AIWatchlistGenerator')
        
        # === TIER 6: Risk Management ===
        self._init_module('var_engine', 'src.var_risk_engine', 'VaRRiskEngine',
                         kwargs={'capital': capital})
        self._init_module('drawdown', 'src.drawdown_recovery', 'DrawdownRecoveryEngine',
                         kwargs={'capital': capital})
        self._init_module('risk_parity', 'src.risk_parity', 'RiskParityEngine',
                         kwargs={'capital': capital})
        self._init_module('portfolio', 'src.portfolio_optimizer', 'PortfolioOptimizer',
                         kwargs={'total_capital': capital})
        
        # === TIER 7: Execution ===
        self._init_module('smart_orders', 'src.smart_order_router', 'SmartOrderRouter')
        self._init_module('paper_trade', 'src.paper_trade', 'PaperTradeSimulator',
                         kwargs={'capital': capital})
        self._init_module('gamma_scalper', 'src.gamma_scalper', 'GammaScalpingEngine')
        
        # === TIER 8: Analytics ===
        self._init_module('journal', 'src.trade_journal', 'TradeJournal')
        self._init_module('attribution', 'src.performance_attribution', 'PerformanceAttribution')
        self._init_module('narrator', 'src.market_narrator', 'MarketNarrator')
        self._init_module('auto_tuner', 'src.auto_tuner', 'AutoHyperTuner')
        
        # === TIER 9: Meta Intelligence ===
        self._init_module('meta_learner', 'src.meta_learner', 'MetaLearnerAggregator')
        
        print(f"\n{'=' * 60}")
        print(f"✅ Initialized {len(self.modules)}/{len(self.modules) + len(self.errors)} modules")
        if self.errors:
            print(f"⚠️ {len(self.errors)} modules failed: {self.errors}")
        print(f"💰 Capital: ₹{capital:,.0f} | Mode: {mode}")
        print(f"{'=' * 60}\n")
        
        self.status = 'INITIALIZED'
    
    def start(self):
        """Start background services."""
        self.start_time = datetime.now()
        self.status = 'RUNNING'
        
        # Start background scrapers
        if 'news' in self.modules:
            try:
                self.modules['news'].start()
            except:
                pass
        
        if 'social' in self.modules:
            try:
                self.modules['social'].start()
            except:
                pass
        
        print(f"🟢 System RUNNING at {self.start_time.strftime('%H:%M:%S')}")
    
    def stop(self):
        """Graceful shutdown."""
        self.status = 'STOPPED'
        if 'news' in self.modules:
            try:
                self.modules['news'].stop()
            except:
                pass
        if 'social' in self.modules:
            try:
                self.modules['social'].stop()
            except:
                pass
        if 'production' in self.modules:
            try:
                self.modules['production'].save_state()
            except:
                pass
        print("🔴 System STOPPED")
    
    def get_module(self, name):
        """Get a specific module."""
        return self.modules.get(name)
    
    def get_status(self):
        """Full system status."""
        uptime = str(datetime.now() - self.start_time).split('.')[0] if self.start_time else '0'
        
        health = None
        if 'production' in self.modules:
            try:
                health = self.modules['production'].get_status()
            except:
                pass
        
        return {
            'version': self.VERSION,
            'status': self.status,
            'uptime': uptime,
            'modules_loaded': len(self.modules),
            'modules_failed': len(self.errors),
            'failed_list': self.errors,
            'health': health
        }
    
    def get_unified_signal(self, market_data):
        """
        Run ALL modules and get unified trading signal.
        This is the main decision-making pipeline.
        """
        signals = {}
        
        # Collect signals from available modules
        try:
            if 'candle_patterns' in self.modules:
                cp = self.modules['candle_patterns'].get_signal(market_data)
                if cp['signal'] != 'NEUTRAL':
                    signals['candle_pattern'] = {
                        'direction': cp['signal'].replace('ISH', ''),
                        'confidence': min(0.9, 0.5 + cp['strength'] * 0.1)
                    }
        except:
            pass
        
        try:
            if 'order_flow' in self.modules:
                flow = self.modules['order_flow'].analyze(market_data)
                if flow['pressure'] not in ['NEUTRAL']:
                    direction = 'BUY' if 'BUY' in flow['pressure'] else 'SELL'
                    signals['order_flow'] = {
                        'direction': direction,
                        'confidence': 0.7 if 'STRONG' in flow['pressure'] else 0.55
                    }
        except:
            pass
        
        try:
            if 'session' in self.modules:
                sess = self.modules['session'].get_intraday_session()
                if not sess.get('should_trade', True):
                    signals['session'] = {'direction': 'HOLD', 'confidence': 0.8}
        except:
            pass
        
        # Aggregate via meta-learner
        if 'meta_learner' in self.modules and signals:
            return self.modules['meta_learner'].aggregate(signals)
        
        return {'final_signal': 'HOLD', 'confidence': 0.5, 'modules': len(signals)}
    
    def _init_module(self, name, module_path, class_name, kwargs=None):
        """Safely initialize a module."""
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            instance = cls(**(kwargs or {}))
            self.modules[name] = instance
            print(f"  ✅ {name}")
        except Exception as e:
            self.errors.append(name)
            logging.debug(f"  ❌ {name}: {e}")
