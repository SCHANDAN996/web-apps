# TradeKaro AI — System Architecture & Developer Guide

## 📐 System Overview

**TradeKaro AI** is an automated algorithmic trading engine built for Indian and Global financial markets. It combines multi-agent AI voting, deep learning (PyTorch), technical indicators, risk management, and real-time reporting.

---

## 🏗️ Core Architecture & Data Flow

```
                     ┌──────────────────────────────┐
                     │   Market Data Feeds          │
                     │ (Shoonya API / Yahoo Finance)│
                     └──────────────┬───────────────┘
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │  Technical Feature Engine    │
                     │  (18 Standardized V4 Features)│
                     └──────────────┬───────────────┘
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │       PyTorch Brain V4       │
                     │  (Tradenet Actor Prediction) │
                     └──────────────┬───────────────┘
                                    │
                                    ▼
 ┌─────────────────────────────────────────────────────────────────────┐
 │                       THE COUNCIL OF AGENTS                         │
 │ ┌───────────────────┐ ┌───────────────────┐ ┌─────────────────────┐ │
 │ │  Macro Analyst    │ │  Sentiment Agent  │ │ Option Chain Agent  │ │
 │ └─────────┬─────────┘ └─────────┬─────────┘ └──────────┬──────────┘ │
 └───────────┼─────────────────────┼──────────────────────┼────────────┘
             │                     │                      │
             └─────────────────────┼──────────────────────┘
                                   │ (Review & Veto)
                                   ▼
                     ┌──────────────────────────────┐
                     │   Risk & Sizing Manager      │
                     │  (Min 60% Conf, Capital Check│
                     └──────────────┬───────────────┘
                                   │
                                   ▼
                     ┌──────────────────────────────┐
                     │ Production Hardener & Retry  │
                     │  (Circuit Breakers, Limiter) │
                     └──────────────┬───────────────┘
                                   │
                                   ▼
                     ┌──────────────────────────────┐
                     │    Shoonya Order Executor    │
                     │ (PAPER / LIVE Order Placement│
                     └──────────────────────────────┘
```

---

## 🧩 Key Subsystems

### 1. Feature Engineering (`config/feature_config.py`)
- Single source of truth for features (`V4_FEATURES`, `v4.0`).
- Consists of 18 normalized technical indicators (`close`, `sma_20`, `ema_50`, `macd`, `adx`, `candle_momentum`, `volume_shock`, `price_velocity`, etc.).

### 2. Multi-Agent Voting Council (`src/agents.py`)
- **Technical Agent**: Deep learning model signal generator.
- **Macro Analyst**: Market regime classification (`BULLISH`, `BEARISH`, `SIDEWAYS_QUIET`, `TRANSITION`).
- **Sentiment Agent**: News and sentiment score analyzer.
- **Option Chain Agent**: Smart Money / Put-Call Ratio tracker.
- **Veto Rule**: Requires >= 60% confidence alignment across agents. Low-confidence trades are automatically vetoed.

### 3. Risk & Position Sizing (`src/risk_manager.py`)
- Volatility-adjusted sizing via ATR.
- Daily loss limit circuit breaker.
- Rejection of low confidence (<0.60) signals.

### 4. Production Hardener (`src/production_hardener.py`)
- Circuit breakers for API, Data, Trade, and Model errors.
- Rate-limiting (max 5 calls/sec).
- Exponential backoff retry logic.

### 5. Exit Notification System (`src/executor.py`)
- Standardized **TRADE CLOSED** notifications with P&L (₹ & %), achieved R:R ratio, holding time, and reason tags.

---

## 🛠️ Developer Commands

- **Run Main Trading Engine**:
  ```bash
  PYTHONPATH=. venv/bin/python main.py
  ```
- **Run Unit Tests**:
  ```bash
  PYTHONPATH=. venv/bin/python tests/test_feature_config.py
  PYTHONPATH=. venv/bin/python tests/test_risk_manager.py
  ```
- **Run Database Maintenance**:
  ```bash
  PYTHONPATH=. venv/bin/python cleanup_db_task.py
  ```
