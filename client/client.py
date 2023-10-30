import aiohttp
from models.subreddit import Subreddit

class RedditClient:
    def __init__(self):
        self.base_url = 'https://www.reddit.com'
        self.subreddits = []

    async def get_subreddit(self, subreddit: str):
        curr_subreddit = Subreddit(subreddit)
        self.subreddits.append(curr_subreddit)
        return curr_subreddit
    
    async def get_subreddits(self, subreddits: list[str]):
        async with aiohttp.ClientSession() as client:
            for subreddit in subreddits:
                curr_subreddit = Subreddit(subreddit)
                await curr_subreddit.get_subreddit()
                self.subreddits.append(curr_subreddit)
        return self.subreddits
            
