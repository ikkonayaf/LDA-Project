from twscrape.api import API
from twscrape.logger import set_log_level

set_log_level("WARNING")

class Scraper:
    def __init__(self):
        self.api = API()
    
    async def search(self, query: str, limit: int = 10):
        tweets = []
        async for tweet in self.api.search(query, limit=limit):
            tweets.append(tweet)
        return tweets
