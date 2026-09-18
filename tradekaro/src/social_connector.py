import random
from datetime import datetime

class SocialDataConnector:
    def __init__(self):
        self.sources = ["Twitter", "Reddit", "NewsAPI"]
        
    def fetch_social_sentiment(self):
        """
        Mock implementation of social sentiment fetching.
        Returns a list of dicts with 'title', 'sentiment_score', etc.
        """
        # In a real app, this would hit X API or Reddit API
        # For now, we return dummy trending topics for the 'Brain' to digest
        signals = []
        
        topics = ["Bitcoin ETF", "NIFTY Bull Run", "Rate Hike Fears", "AI Stock Boom", "OPEC Meeting"]
        
        for topic in topics:
            score = random.uniform(-0.8, 0.9)
            signals.append({
                "symbol": "BTC" if "Bitcoin" in topic else "NIFTY",
                "title": f"Viral Topic: {topic} trending on social media",
                "publisher": random.choice(self.sources),
                "link": "http://twitter.com/search?q=" + topic.replace(" ", "%20"),
                "publish_time": datetime.now(),
                "type": "social",
                "sentiment_score": score
            })
            
        return signals
