from datetime import datetime
import re
try:
    from .comment import Comment
    from .media import Media
except ImportError:
    from comment import Comment
    from media import Media
import aiohttp

SUBREDDIT_ORDERING = ['hot', 'new', 'rising', 'controversial', 'top']

class Post:
    def __init__(self, subreddit, post_id):
        self.base_url = 'https://www.reddit.com/r/{subreddit}/comments/{post_id}.json?sort={sort}&limit=1000'
        self.morechildren_url = "https://old.reddit.com/api/morechildren?api_type=json&link_id=t3_{POST_ID}&children={more_id}"
        self.subreddit = subreddit
        self.post_id = post_id
        self.isSynced = False
        self.return_data = None
        self.comments = []
        self.post = None
        self.medias = []

    async def get_json(self, client, url):
        async with client.get(url) as response:
            # print(response)
            assert response.status == 200
            return await response.json()

    async def sync(self, comment_sorting:str = 'new'):
        url = self.base_url.format(subreddit=self.subreddit, post_id=self.post_id, sort=comment_sorting)
        async with aiohttp.ClientSession() as client:
            data = await self.get_json(client, url)
            self.return_data = data
            self.isSynced = True
            await self.normalize_post()
            await self.get_comments()
            
    async def normalize_post(self):
        if not self.isSynced:
            await self.sync()
            return
        
        post = self.return_data[0]['data']['children'][0]['data']
        self.post = {
            'datetime': datetime.utcfromtimestamp(post['created']).isoformat(),
            'title': post['title'],
            'text': post['selftext'],
            'subreddit': post['subreddit'],
            'permalink': post['permalink'],
            'post_id': post['name'],
            'username': post['author'],
            'author_id': post['author_fullname'],
            'id': post['id'],
            'num_comments': int(post['num_comments']),
            'score': int(post['score'])
        }
        self.medias = Media.from_json(post)
        

    async def get_json_comments(self, comment:dict[str, any]):
        comments = []
        more_ids = []

        if 'body' not in comment:
            return [], []
        
        comments.append(Comment.from_json_api(comment))

        if 'replies' in comment and comment['replies'] != '':
            for reply in comment['replies']['data']['children']:
                if reply['kind'] == 't1':
                    reply_comments, reply_more_ids = await self.get_json_comments(reply['data'])
                    comments.extend(reply_comments)
                    more_ids.extend(reply_more_ids)  # Acumula os IDs do tipo "more" das respostas
                elif reply['kind'] == 'more':
                    more_ids.extend(reply['data']['children'])

        return comments, more_ids
    

    async def get_morechildren_comments(self, more_ids:list[str], client:aiohttp.ClientSession):
        more_comments = []
        even_more = []
        for i in range(0, len(more_ids), 100):
            more_ids_str = ','.join(more_ids[i:i+100])
            more_data = await self.get_json(client, self.morechildren_url.format(POST_ID=self.post_id, more_id=more_ids_str))
            
            for comment in more_data['json']['data']['things']:
                if comment['kind'] == 't1':
                    more_comments.append(Comment.from_morechildren_api(comment['data']))
                    
                elif comment['kind'] == 'more':
                    match_ids = re.search(r"morechildren\((.*?)\)", comment['data']['content'])
                    
                    if match_ids:
                        new_ids = match_ids.group(1).split(', ')[3].replace("'", '').split(',')
                        even_more.extend(new_ids)
        
        if even_more:
            even_more_comments = await self.get_morechildren_comments(even_more, client)
            more_comments.extend(even_more_comments)

        return more_comments


    async def get_comments(self, sync:bool = True):
        if not sync and self.isSynced:
            return self.comments
        
        if sync and not self.isSynced:
            await self.sync()

        comments = []
        more_ids = []

        for child in self.return_data[1]['data']['children']:
            if child['kind'] == 't1':
                curr_comments, curr_more_ids = await self.get_json_comments(child['data'])
                comments.extend(curr_comments)
                more_ids.extend(curr_more_ids)
            elif child['kind'] == 'more':
                more_ids.extend(child['data']['children'])

        if more_ids:
            with aiohttp.ClientSession() as client:
                more_comments = await self.get_morechildren_comments(more_ids, client)
                comments.extend(more_comments)
        
        self.comments = comments
        return comments
