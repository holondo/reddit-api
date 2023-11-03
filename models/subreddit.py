import aiohttp
try:
    from .post import Post
except ImportError:
    from post import Post

SUBREDDIT_ORDERING = ['hot', 'new', 'rising', 'controversial', 'top']

class Subreddit:
    def __init__(self, subreddit_name: str):
        self.subreddit_name = subreddit_name
        self.base_url = f'https://www.reddit.com/r/{self.subreddit_name}/'
        self.posts = []
        self.isSynced = False
        self.ordering = 'new'

    async def get_json(self, client, url):
        async with client.get(url+'.json') as response:
            assert response.status == 200
            return await response.json()

    async def get_subreddit(self, ordering: str = 'new', limit: int = 25):
        if ordering not in SUBREDDIT_ORDERING:
            raise ValueError(f'Invalid ordering: {ordering}')
        self.ordering = ordering
        url = f'{self.base_url}{ordering}.json?count={limit}'
        async with aiohttp.ClientSession() as client:
            print(url)
            data = await self.get_json(client, url)
        
        self.posts = [Post(self.subreddit_name, post['data']['id']) for post in data['data']['children']]
        return self.posts
    
    async def get_next_posts(self, limit: int = 25):
        if not self.posts:
            raise ValueError('No posts to get')
        last_post = self.posts[-1]
        after = f't3_{last_post.post_id}'
        url = f'{self.base_url}{self.ordering}.json?after={after}&count={limit}'
        async with aiohttp.ClientSession() as client:
            data = await self.get_json(client, url)
        
        new_posts = [Post(self.subreddit_name, post['data']['id']) for post in data['data']['children']]
        self.posts.extend(new_posts)
        return self.posts

    async def get_n_posts(self, n: int = 25):
        # count = 0
        if not self.posts:
            await self.get_subreddit()
        
        last_post_id = self.posts[-1].post_id

        while len(self.posts) < n:
            await self.get_next_posts()
            if last_post_id == self.posts[-1].post_id:
                break
            last_post_id = self.posts[-1].post_id
        
        return self.posts

    async def get_post(self, post_id: str):
        try:
            post = Post(self.subreddit_name, post_id)
            await post.sync()
            return post
        except:
            raise ValueError(f'Invalid post_id: {post_id}')
        
    async def syncPosts(self):
        
        for post in self.posts:
            await post.sync()
        self.isSynced = True
        return self.posts