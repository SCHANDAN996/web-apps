"""
📰 News Scraper + Event Calendar — Auto-Fetch Market Events

Sources:
  - MoneyControl RSS (free, no API key needed)
  - NSE circulars
  - RBI announcements (RSS feed)
  - Economic calendar (key dates)

Features:
  - Auto-scrape every 15 minutes
  - Event impact classification (HIGH/MEDIUM/LOW)
  - Pre-built calendar: RBI policy, Budget, Expiry, Results season
"""

import re
import time
import logging
import threading
from datetime import datetime, timedelta
from collections import deque

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class NewsEventScraper:
    """
    Auto-scrapes financial news and maintains event calendar.
    
    Usage:
        scraper = NewsEventScraper()
        scraper.start()  # Background scraping every 15 min
        headlines = scraper.get_latest(10)
        events = scraper.get_upcoming_events()
    """
    
    # RSS/Atom feeds (free, no API required)
    NEWS_SOURCES = {
        'moneycontrol': 'https://www.moneycontrol.com/rss/marketreports.xml',
        'moneycontrol_news': 'https://www.moneycontrol.com/rss/latestnews.xml',
        'et_markets': 'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms',
    }
    
    # Pre-built event calendar 2026 (approximate dates)
    EVENT_CALENDAR = [
        {'date': '2026-02-01', 'event': 'Union Budget', 'impact': 'HIGH', 'sector': 'ALL'},
        {'date': '2026-04-01', 'event': 'RBI Policy Meeting', 'impact': 'HIGH', 'sector': 'BANKS'},
        {'date': '2026-06-01', 'event': 'RBI Policy Meeting', 'impact': 'HIGH', 'sector': 'BANKS'},
        {'date': '2026-08-01', 'event': 'RBI Policy Meeting', 'impact': 'HIGH', 'sector': 'BANKS'},
        {'date': '2026-10-01', 'event': 'RBI Policy Meeting', 'impact': 'HIGH', 'sector': 'BANKS'},
        {'date': '2026-12-01', 'event': 'RBI Policy Meeting', 'impact': 'HIGH', 'sector': 'BANKS'},
        # Monthly expiry days (last Thursday)
        {'date': '2026-01-29', 'event': 'Monthly Expiry', 'impact': 'MEDIUM', 'sector': 'ALL'},
        {'date': '2026-02-26', 'event': 'Monthly Expiry', 'impact': 'MEDIUM', 'sector': 'ALL'},
        {'date': '2026-03-26', 'event': 'Monthly Expiry', 'impact': 'MEDIUM', 'sector': 'ALL'},
        {'date': '2026-04-30', 'event': 'Monthly Expiry', 'impact': 'MEDIUM', 'sector': 'ALL'},
        # Results season
        {'date': '2026-01-15', 'event': 'Q3 Results Season Start', 'impact': 'MEDIUM', 'sector': 'ALL'},
        {'date': '2026-04-15', 'event': 'Q4 Results Season Start', 'impact': 'MEDIUM', 'sector': 'ALL'},
        {'date': '2026-07-15', 'event': 'Q1 Results Season Start', 'impact': 'MEDIUM', 'sector': 'ALL'},
        {'date': '2026-10-15', 'event': 'Q2 Results Season Start', 'impact': 'MEDIUM', 'sector': 'ALL'},
    ]
    
    # Keywords for impact classification
    HIGH_IMPACT_KEYWORDS = [
        'rbi', 'rate cut', 'rate hike', 'budget', 'gdp', 'inflation', 'fed',
        'crash', 'circuit', 'halt', 'ban', 'war', 'sanction', 'default',
        'sebi', 'scam', 'fraud', 'emergency'
    ]
    
    MEDIUM_IMPACT_KEYWORDS = [
        'quarterly', 'results', 'earnings', 'dividend', 'buyback', 'fii',
        'dii', 'ipo', 'listing', 'upgrade', 'downgrade', 'expiry',
        'nifty', 'banknifty', 'sensex'
    ]
    
    def __init__(self, db=None, interval_min=15):
        self.db = db
        self.interval = interval_min * 60
        self.headlines = deque(maxlen=500)
        self.running = False
        self._thread = None
    
    def start(self):
        """Start background scraping."""
        self.running = True
        self._thread = threading.Thread(target=self._scrape_loop, daemon=True)
        self._thread.start()
        print(f"[News] 📰 Scraper started (every {self.interval//60} min)")
    
    def stop(self):
        self.running = False
    
    def scrape_now(self):
        """Force immediate scrape."""
        for name, url in self.NEWS_SOURCES.items():
            try:
                headlines = self._fetch_rss(url)
                for h in headlines:
                    h['source'] = name
                    h['impact'] = self._classify_impact(h['title'])
                    h['fetched'] = datetime.now().isoformat()
                    self.headlines.append(h)
                    
                    if self.db:
                        try:
                            self.db.store_news(h)
                        except:
                            pass
            except Exception as e:
                logging.debug(f"[News] {name} scrape failed: {e}")
    
    def get_latest(self, n=20):
        """Get most recent N headlines."""
        return list(self.headlines)[-n:]
    
    def get_by_impact(self, impact='HIGH'):
        """Get headlines by impact level."""
        return [h for h in self.headlines if h.get('impact') == impact]
    
    def get_upcoming_events(self, days=7):
        """Get events happening in the next N days."""
        now = datetime.now()
        cutoff = now + timedelta(days=days)
        
        upcoming = []
        for event in self.EVENT_CALENDAR:
            try:
                event_date = datetime.strptime(event['date'], '%Y-%m-%d')
                if now <= event_date <= cutoff:
                    event_copy = event.copy()
                    event_copy['days_until'] = (event_date - now).days
                    upcoming.append(event_copy)
            except:
                pass
        
        return sorted(upcoming, key=lambda x: x['days_until'])
    
    def is_event_day(self):
        """Check if today is a high-impact event day."""
        today = datetime.now().strftime('%Y-%m-%d')
        for event in self.EVENT_CALENDAR:
            if event['date'] == today and event['impact'] == 'HIGH':
                return True, event['event']
        return False, None
    
    def _scrape_loop(self):
        while self.running:
            self.scrape_now()
            time.sleep(self.interval)
    
    def _fetch_rss(self, url):
        """Parse RSS XML feed (simple regex parser, no lxml needed)."""
        if not HAS_REQUESTS:
            return []
        
        resp = requests.get(url, timeout=10, headers={
            'User-Agent': 'TradeKaro-AI/1.0'
        })
        
        headlines = []
        # Simple XML parsing with regex (avoids lxml dependency)
        items = re.findall(r'<item>(.*?)</item>', resp.text, re.DOTALL)
        
        for item in items[:30]:
            title = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>', item)
            if not title:
                title = re.search(r'<title>(.*?)</title>', item)
            
            link = re.search(r'<link>(.*?)</link>', item)
            pub_date = re.search(r'<pubDate>(.*?)</pubDate>', item)
            
            if title:
                headlines.append({
                    'title': title.group(1).strip(),
                    'link': link.group(1).strip() if link else '',
                    'pub_date': pub_date.group(1).strip() if pub_date else ''
                })
        
        return headlines
    
    def _classify_impact(self, title):
        """Classify news impact level by keywords."""
        title_lower = title.lower()
        
        for kw in self.HIGH_IMPACT_KEYWORDS:
            if kw in title_lower:
                return 'HIGH'
        
        for kw in self.MEDIUM_IMPACT_KEYWORDS:
            if kw in title_lower:
                return 'MEDIUM'
        
        return 'LOW'
