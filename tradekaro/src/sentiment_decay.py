"""
⏳ Sentiment Decay Tracker — How Quickly Does News Impact Fade?

Not all news affects price the same way or duration:
  - Earnings: impact lasts 3-5 days
  - RBI policy: impact lasts 1-2 weeks
  - Rumors: impact fades in hours
  - War/crisis: impact lasts weeks-months

Tracks each news event and measures its decaying impact on price.
"""

import math
from datetime import datetime, timedelta
from collections import deque


class SentimentDecayTracker:
    """
    Tracks how news sentiment decays over time.
    
    Usage:
        tracker = SentimentDecayTracker()
        tracker.add_event('RBI rate cut', impact=0.8, category='MACRO')
        current = tracker.get_active_sentiment()
        # 0.6 (decayed from 0.8)
    """
    
    # Half-life for different event categories (in hours)
    DECAY_RATES = {
        'RUMOR':       2,     # Fades in hours
        'NEWS':        12,    # Fades in half a day
        'EARNINGS':    72,    # Lasts 3 days
        'MACRO':       168,   # 1 week (RBI, Fed, GDP)
        'CRISIS':      720,   # 1 month (war, pandemic)
        'STRUCTURAL':  2160,  # 3 months (budget, regulation)
    }
    
    def __init__(self):
        self.events = deque(maxlen=200)
    
    def add_event(self, title, impact, category='NEWS', direction='BULLISH'):
        """
        Record a news event with initial impact.
        
        Args:
            title: Event description
            impact: Initial impact 0-1
            category: One of DECAY_RATES keys
            direction: BULLISH or BEARISH
        """
        sign = 1 if direction == 'BULLISH' else -1
        
        self.events.append({
            'title': title,
            'impact': impact * sign,
            'category': category,
            'half_life': self.DECAY_RATES.get(category, 12),
            'created': datetime.now(),
            'direction': direction
        })
    
    def get_active_sentiment(self):
        """
        Get current aggregate sentiment from all active (non-decayed) events.
        """
        now = datetime.now()
        total = 0
        
        for event in self.events:
            hours_elapsed = (now - event['created']).total_seconds() / 3600
            half_life = event['half_life']
            
            # Exponential decay: impact * 0.5^(t/half_life)
            decayed = event['impact'] * math.pow(0.5, hours_elapsed / half_life)
            
            if abs(decayed) > 0.01:  # Still significant
                total += decayed
        
        return round(max(-1, min(1, total)), 4)
    
    def get_active_events(self, min_impact=0.05):
        """Get list of events still affecting the market."""
        now = datetime.now()
        active = []
        
        for event in self.events:
            hours = (now - event['created']).total_seconds() / 3600
            decayed = abs(event['impact']) * math.pow(0.5, hours / event['half_life'])
            
            if decayed > min_impact:
                active.append({
                    'title': event['title'],
                    'original_impact': abs(event['impact']),
                    'current_impact': round(decayed, 3),
                    'decay_pct': round((1 - decayed / abs(event['impact'])) * 100, 1),
                    'direction': event['direction'],
                    'hours_active': round(hours, 1),
                    'hours_remaining': round(event['half_life'] * 3, 1)  # ~12.5% left
                })
        
        return sorted(active, key=lambda x: x['current_impact'], reverse=True)
    
    def get_dominant_event(self):
        """Get the single most impactful active event."""
        active = self.get_active_events()
        return active[0] if active else None
