"""
📰 FinBERT Sentiment Analyzer — Deep NLP for Financial Text

Why FinBERT over TextBlob?
  TextBlob: "RBI hikes rates" → Polarity: -0.1 (WRONG — thinks "hikes" is negative)
  FinBERT: "RBI hikes rates" → {negative: 0.85, neutral: 0.10, positive: 0.05} (CORRECT)

FinBERT is pretrained on 46K+ financial news articles.
It understands financial context, negation, and market-specific language.

Usage:
    analyzer = FinBERTSentiment()
    result = analyzer.analyze("NIFTY rallies 500 points on RBI policy")
    # {'label': 'positive', 'score': 0.92, 'positive': 0.92, 'negative': 0.03, 'neutral': 0.05}
"""

import os
import json
import logging
from datetime import datetime
from collections import deque

# Lazy loading — FinBERT is heavy (~420MB). Only load when first used.
_finbert_model = None
_finbert_tokenizer = None
_finbert_available = None


def _check_finbert_available():
    """Check if transformers library is installed."""
    global _finbert_available
    if _finbert_available is not None:
        return _finbert_available
    try:
        import transformers
        _finbert_available = True
    except ImportError:
        _finbert_available = False
        logging.warning("[FinBERT] transformers library not installed. Using fallback.")
    return _finbert_available


def _load_finbert():
    """Lazy-load FinBERT model (downloads ~420MB on first use)."""
    global _finbert_model, _finbert_tokenizer
    
    if _finbert_model is not None:
        return _finbert_model, _finbert_tokenizer
    
    if not _check_finbert_available():
        return None, None
    
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        import torch
        
        model_name = "ProsusAI/finbert"
        cache_dir = "models/finbert_cache"
        
        print("[FinBERT] 📥 Loading FinBERT model (first time may take a few minutes)...")
        
        _finbert_tokenizer = AutoTokenizer.from_pretrained(
            model_name, cache_dir=cache_dir
        )
        _finbert_model = AutoModelForSequenceClassification.from_pretrained(
            model_name, cache_dir=cache_dir
        )
        _finbert_model.eval()
        
        print("[FinBERT] ✅ Model loaded successfully!")
        return _finbert_model, _finbert_tokenizer
        
    except Exception as e:
        logging.error(f"[FinBERT] Failed to load: {e}")
        return None, None


class FinBERTSentiment:
    """
    Financial sentiment analyzer using FinBERT.
    
    Features:
    - Deep NLP (understands financial context + negation)
    - Batch analysis for multiple headlines
    - News impact memory (same headline type → similar market reaction)
    - Sentiment momentum tracking (is fear increasing or decreasing?)
    - Graceful fallback to keyword-based if FinBERT unavailable
    """
    
    IMPACT_MEMORY_FILE = 'models/news_impact_memory.json'
    LABELS = ['positive', 'negative', 'neutral']
    
    def __init__(self, use_finbert=True):
        self.use_finbert = use_finbert and _check_finbert_available()
        
        # Sentiment momentum (track last N sentiment scores)
        self.sentiment_history = deque(maxlen=50)
        
        # News impact memory: {keyword_hash: avg_market_impact}
        self.impact_memory = self._load_impact_memory()
        
        if self.use_finbert:
            print("[FinBERT] 🧠 Deep NLP mode active")
        else:
            print("[FinBERT] ⚠️ Fallback to keyword-based sentiment")
    
    def analyze(self, text):
        """
        Analyze sentiment of financial text.
        
        Returns:
            dict: {label, score, positive, negative, neutral, momentum}
        """
        if not text or len(text.strip()) < 5:
            return self._neutral_result()
        
        if self.use_finbert:
            result = self._analyze_finbert(text)
        else:
            result = self._analyze_keyword(text)
        
        # Track momentum
        if result['label'] == 'positive':
            self.sentiment_history.append(result['score'])
        elif result['label'] == 'negative':
            self.sentiment_history.append(-result['score'])
        else:
            self.sentiment_history.append(0)
        
        # Calculate momentum
        if len(self.sentiment_history) >= 5:
            recent = list(self.sentiment_history)[-5:]
            older = list(self.sentiment_history)[-10:-5] if len(self.sentiment_history) >= 10 else [0]
            result['momentum'] = sum(recent)/len(recent) - sum(older)/len(older)
        else:
            result['momentum'] = 0
        
        return result
    
    def analyze_batch(self, texts):
        """Analyze multiple headlines, return aggregate sentiment."""
        if not texts:
            return self._neutral_result()
        
        results = [self.analyze(t) for t in texts]
        
        # Aggregate
        avg_pos = sum(r['positive'] for r in results) / len(results)
        avg_neg = sum(r['negative'] for r in results) / len(results)
        avg_neu = sum(r['neutral'] for r in results) / len(results)
        
        # Net sentiment: positive - negative
        net = avg_pos - avg_neg
        
        if net > 0.1:
            label = 'positive'
        elif net < -0.1:
            label = 'negative'
        else:
            label = 'neutral'
        
        return {
            'label': label,
            'score': abs(net),
            'positive': round(avg_pos, 4),
            'negative': round(avg_neg, 4),
            'neutral': round(avg_neu, 4),
            'net_sentiment': round(net, 4),
            'num_articles': len(texts),
            'momentum': results[-1].get('momentum', 0) if results else 0
        }
    
    def record_market_impact(self, text, market_move_pct):
        """Record how a news type actually affected the market (for learning)."""
        key = self._text_to_key(text)
        if key not in self.impact_memory:
            self.impact_memory[key] = {'impacts': [], 'avg_impact': 0}
        
        self.impact_memory[key]['impacts'].append(market_move_pct)
        # Keep last 10 impacts
        self.impact_memory[key]['impacts'] = self.impact_memory[key]['impacts'][-10:]
        self.impact_memory[key]['avg_impact'] = sum(
            self.impact_memory[key]['impacts']
        ) / len(self.impact_memory[key]['impacts'])
        
        self._save_impact_memory()
    
    def get_expected_impact(self, text):
        """Get expected market impact based on similar past news."""
        key = self._text_to_key(text)
        if key in self.impact_memory:
            return self.impact_memory[key]['avg_impact']
        return 0
    
    def _analyze_finbert(self, text):
        """FinBERT deep analysis."""
        import torch
        
        model, tokenizer = _load_finbert()
        if model is None:
            return self._analyze_keyword(text)
        
        try:
            # Truncate to 512 tokens
            inputs = tokenizer(text, return_tensors="pt", truncation=True, 
                             max_length=512, padding=True)
            
            with torch.no_grad():
                outputs = model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            scores = probs[0].tolist()
            # FinBERT outputs: [positive, negative, neutral]
            
            label_idx = scores.index(max(scores))
            
            return {
                'label': self.LABELS[label_idx],
                'score': round(max(scores), 4),
                'positive': round(scores[0], 4),
                'negative': round(scores[1], 4),
                'neutral': round(scores[2], 4)
            }
        except Exception as e:
            logging.error(f"[FinBERT] Analysis error: {e}")
            return self._analyze_keyword(text)
    
    def _analyze_keyword(self, text):
        """Fallback keyword-based sentiment (better than TextBlob for finance)."""
        text_lower = text.lower()
        
        bullish_words = [
            'rally', 'surge', 'soar', 'breakout', 'gain', 'bullish', 'upside',
            'upgrade', 'beat', 'outperform', 'growth', 'profit', 'record high',
            'stimulus', 'rate cut', 'buy', 'accumulate', 'strong', 'recovery',
            'boom', 'optimism', 'positive', 'up', 'rise', 'higher', 'advance'
        ]
        
        bearish_words = [
            'crash', 'plunge', 'slump', 'breakdown', 'loss', 'bearish', 'downside',
            'downgrade', 'miss', 'underperform', 'recession', 'crisis', 'sell',
            'rate hike', 'inflation', 'weak', 'decline', 'fear', 'panic', 'warning',
            'war', 'sanctions', 'default', 'fall', 'lower', 'drop', 'plummet'
        ]
        
        negation_words = ['not', 'no', "n't", 'never', 'without', 'despite']
        
        # Check for negation
        has_negation = any(neg in text_lower for neg in negation_words)
        
        bull_count = sum(1 for w in bullish_words if w in text_lower)
        bear_count = sum(1 for w in bearish_words if w in text_lower)
        
        # Flip if negation detected
        if has_negation:
            bull_count, bear_count = bear_count, bull_count
        
        total = bull_count + bear_count + 1  # +1 to avoid division by zero
        pos_score = bull_count / total
        neg_score = bear_count / total
        neu_score = 1 - pos_score - neg_score
        
        if bull_count > bear_count:
            label = 'positive'
        elif bear_count > bull_count:
            label = 'negative'
        else:
            label = 'neutral'
        
        return {
            'label': label,
            'score': round(max(pos_score, neg_score, neu_score), 4),
            'positive': round(pos_score, 4),
            'negative': round(neg_score, 4),
            'neutral': round(max(0, neu_score), 4)
        }
    
    def _neutral_result(self):
        return {
            'label': 'neutral', 'score': 1.0,
            'positive': 0, 'negative': 0, 'neutral': 1.0,
            'momentum': 0
        }
    
    def _text_to_key(self, text):
        """Create a keyword hash from text for impact memory."""
        words = text.lower().split()
        key_words = [w for w in words if len(w) > 3][:5]
        return '_'.join(sorted(key_words))
    
    def _load_impact_memory(self):
        if os.path.exists(self.IMPACT_MEMORY_FILE):
            try:
                with open(self.IMPACT_MEMORY_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_impact_memory(self):
        try:
            os.makedirs(os.path.dirname(self.IMPACT_MEMORY_FILE) or 'models', exist_ok=True)
            with open(self.IMPACT_MEMORY_FILE, 'w') as f:
                json.dump(self.impact_memory, f)
        except:
            pass
