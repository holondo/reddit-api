from datetime import datetime
try:
    from .media import Media
except ImportError:
    from media import Media
import re

COMMENTS_FIELDS = ['created', 'permalink', 'name', 'body', 'author', 'id', 'author_fullname', 'parent_id', 'score', "media_metadata", "media", "url", "link_id"]
JSON_FIELD_TRANSLATION = {
    'created': 'datetime',
    'permalink': 'c_url',
    'name': 'comment_id',
    'body': 'text',
    'author': 'username',
    'id': 'id',
    'author_fullname': 'author_id',
    'parent_id': 'reply_to',
    'score': 'score',
    "media_metadata": "media_metadata",
    "media": "media",
    "url": "url",
    "link_id": "post_id"
}

MORECHILDREN_FIELD_TRANSLATION = {
    'datetime' : 'datetime',
    'contentText' : 'text',
    'permalink' : 'c_url',
    'comment_id' : 'comment_id',
    'username' : 'username',
    'author_id' : 'author_id',
    'parent' : 'reply_to',
    'id' : 'id',
    'score' : 'score',
    'link' : 'post_id'
}


class Comment:
    def __init__(self, data:dict[str, any], comment_fields:list[str] = COMMENTS_FIELDS) -> None:
        self.data = data
        self.comment_fields = comment_fields
        self.medias = []

        # self.text = data['text']
        # self.datetime = data['datetime']

    
    def to_dict(self):
        medias_dicts = [media.to_dict() for media in self.medias if self.medias]
        return {
            **self.data,
            'medias' : medias_dicts
        }



    @classmethod
    def from_json_api(cls, data:dict[str, any], comment_fields:list[str] = COMMENTS_FIELDS, field_translation:dict[str, str] = JSON_FIELD_TRANSLATION):
        comment_data = {
            field_translation[field]: data[field] for field in comment_fields if field in data
        }
        comment_data['datetime'] = datetime.utcfromtimestamp(comment_data['datetime']).isoformat()
        medias = cls.get_comment_gif(data)
        instance = cls(comment_data, comment_fields)
        instance.medias = medias
        return instance
    
    @classmethod
    def from_morechildren_api(cls, data:dict[str, any], comment_fields:list[str] = COMMENTS_FIELDS, field_translation:dict[str, str] = JSON_FIELD_TRANSLATION):
        normalized = {}
        if not data.get('data', None):
            return normalized
        
        comment_data = {**data['data'], **Comment._comment_html_content_to_dict_(data['data']['content'])}
        
        try:
            normalized = {
                'datetime' : datetime.strptime(comment_data['datetime'], '%a %b %d %H:%M:%S %Y %Z').isoformat(),
                'text' : comment_data['contentText'],
                'c_url' : comment_data['permalink'],
                'comment_id' : comment_data['comment_id'],
                'username' : comment_data['username'],
                'author_id' : comment_data['author_id'],
                'reply_to' : comment_data['parent'],
                'id' : comment_data['id'],
                'score' : int(comment_data['score'] if comment_data['score'] else '0'),
                'post_id' : comment_data['link']
            }

            return cls(normalized, comment_fields)
        except:
            print(comment_data)

        return cls(normalized, comment_fields)
    
    @classmethod
    def _comment_html_content_to_dict_(cls, content:str):

        def get_match(pattern:str, content:str):
            match = re.search(pattern, content)
            return match.group(1) if match else ''

        data_dict = {
            "datetime": get_match(r'&lt;time title=\"(.*?)\" datetime', content),
            "permalink": get_match(r'data-permalink=\"(.*?)\"', content),
            "comment_id": get_match(r'data-fullname=\"(.*?)\"', content),
            "text": get_match(r'&lt;div class=\"md\"&gt;(.*?)&lt;/div&gt;', content).replace('&lt;p&gt;', '\n').replace('&lt;/p&gt;', '\n'),
            "username": get_match(r'data-author=\"(.*?)\"', content),
            "id": get_match(r'data-fullname=\"(.*?)\"', content).split('_')[1] if get_match(r'data-fullname=\"(.*?)\"', content) else '',
            "author_id": get_match(r'data-author-fullname=\"(.*?)\"', content),
            # "parent_id": "",
            "score": get_match(r'&lt;span class=\"score unvoted\" title=\"(.*?)\"&gt;', content).split(' ')[0]
        }
        

        return data_dict

    @classmethod
    def get_comment_gif(cls, comment:dict[str, any]):
        medias = []
        comment_id = comment['id']
        try:
            if 'media_metadata' in comment:
                for media in comment['media_metadata']:
                    medias.append(Media(comment_id, comment['link_id'], comment['media_metadata'][media]['s']['gif'], 'gif', None))
                    
        except:
            comment['media_metadata'][media]

        return medias