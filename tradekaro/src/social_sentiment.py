"""
🌐 Social Sentiment Heatmap — Twitter/Reddit/StockTwits Sentiment Scraping

Scrapes public sentiment from multiple sources:
  - Google Trends (interest over time for stock names)
  - Reddit (popular finance subreddits via JSON API)
  - Financial news sentiment aggregation

Generates a heatmap: which stocks are trending + bullish/bearish?
"""

import re
import time
import logging
import threading
from datetime import datetime
from collections import defaultdict, deque

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class SocialSentimentHeatmap:
    """
    Aggregates social media sentiment across multiple sources.
    
    Usage:
        heatmap = SocialSentimentHeatmap()
        heatmap.start()
        data = heatmap.get_heatmap()
        # {'RELIANCE': {'buzz': 85, 'sentiment': 0.6, 'trending': True}, ...}
    """
    
    # Stock name → common social media references
    STOCK_ALIASES = {
        'RELIANCE':  ['reliance', 'ril', 'jio', 'mukesh ambani'],
        'TCS':       ['tcs', 'tata consultancy'],
        'HDFCBANK':  ['hdfc bank', 'hdfcbank', 'hdfc'],
        'INFY':      ['infosys', 'infy', 'narayana murthy'],
        'ICICIBANK': ['icici bank', 'icicibank', 'icici'],
        'SBIN':      ['sbi', 'state bank', 'sbin'],
        'TATAMOTORS':['tata motors', 'tatamotors', 'tata cars'],
        'NIFTY':     ['nifty', 'nifty50', 'nifty 50'],
        'BANKNIFTY': ['banknifty', 'bank nifty'],
        'ADANI':     ['adani', 'adanient', 'gautam adani'],
    }
    
    # Reddit finance subreddits (public JSON API, no auth needed)
    REDDIT_SUBS = [
        'IndianStreetBets',
        'IndiaInvestments',
        'DalalStreetTalks',
    ]
    
    BULLISH_KEYWORDS = [
        'bull', 'buy', 'long', 'moon', 'rocket', 'breakout', 'rally',
        'gains', 'profit', 'up', 'strong', 'bullish', 'accumulate',
        'target', 'buy call', 'calls', 'support', 'oversold'
    ]
    
    BEARISH_KEYWORDS = [
        'bear', 'sell', 'short', 'crash', 'dump', 'breakdown', 'fall',
        'loss', 'down', 'weak', 'bearish', 'avoid', 'resistance',
        'overbought', 'puts', 'buy put', 'panic'
    ]
    
    def __init__(self, scrape_interval_min=30):
        self.interval = scrape_interval_min * 60
        self.stock_buzz = defaultdict(lambda: {
            'mentions': 0, 'bullish': 0, 'bearish': 0, 
            'neutral': 0, 'posts': deque(maxlen=50)
        })
        self.running = False
        self._thread = None
    
    def start(self):
        """Start background scraping."""
        self.running = True
        self._thread = threading.Thread(target=self._scrape_loop, daemon=True)
        self._thread.start()
        print("[Social] 🌐 Sentiment scraping started")
    
    def stop(self):
        self.running = False
    
    def scrape_now(self):
        """Force immediate scrape from all sources."""
        self._scrape_reddit()
    
    def get_heatmap(self):
        """Get current sentiment heatmap for all tracked stocks."""
        heatmap = {}
        for stock, data in self.stock_buzz.items():
            total = data['bullish'] + data['bearish'] + data['neutral']
            if total == 0:
                continue
            
            sentiment = (data['bullish'] - data['bearish']) / max(total, 1)
            
            heatmap[stock] = {
                'buzz': data['mentions'],
                'sentiment': round(sentiment, 3),
                'bullish_pct': round(data['bullish'] / max(total, 1) * 100, 1),
                'bearish_pct': round(data['bearish'] / max(total, 1) * 100, 1),
                'trending': data['mentions'] > 5,
                'signal': 'BULLISH' if sentiment > 0.3 else 'BEARISH' if sentiment < -0.3 else 'NEUTRAL'
            }
        
        # Sort by buzz
        return dict(sorted(heatmap.items(), key=lambda x: x[1]['buzz'], reverse=True))
    
    def get_trending(self, top_n=5):
        """Get top N trending stocks by social buzz."""
        heatmap = self.get_heatmap()
        return dict(list(heatmap.items())[:top_n])
    
    def _scrape_reddit(self):
        """Scrape Reddit finance subs (public JSON API)."""
        if not HAS_REQUESTS:
            return
        
        for sub in self.REDDIT_SUBS:
            try:
                url = f"https://www.reddit.com/r/{sub}/hot.json?limit=25"
                resp = requests.get(url, headers={
                    'User-Agent': 'TradeKaro-AI/1.0'
                }, timeout=10)
                
                if resp.status_code != 200:
                    continue
                
                posts = resp.json().get('data', {}).get('children', [])
                
                for post in posts:
                    pdata = post.get('data', {})
                    title = pdata.get('title', '')
                    body = pdata.get('selftext', '')
                    text = f"{title} {body}".lower()
                    
                    # Match against stock aliases
                    for stock, aliases in self.STOCK_ALIASES.items():
                        if any(alias in text for alias in aliases):
                            self.stock_buzz[stock]['mentions'] += 1
                            
                            # Classify sentiment
                            bull = sum(1 for kw in self.BULLISH_KEYWORDS if kw in text)
                            bear = sum(1 for kw in self.BEARISH_KEYWORDS if kw in text)
                            
                            if bull > bear:
                                self.stock_buzz[stock]['bullish'] += 1
                            elif bear > bull:
                                self.stock_buzz[stock]['bearish'] += 1
                            else:
                                self.stock_buzz[stock]['neutral'] += 1
                            
                            self.stock_buzz[stock]['posts'].append({
                                'title': title[:100],
                                'source': f"r/{sub}",
                                'time': datetime.now().isoformat()
                            })
            except Exception as e:
                logging.debug(f"[Social] Reddit {sub} error: {e}")
    
    def _scrape_loop(self):
        while self.running:
            self.scrape_now()
            time.sleep(self.interval)
