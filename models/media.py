class Media:
    def __init__(self, post_id, media_url, media_type, caption=None):
        self.post_id = post_id
        self.media_url = media_url
        self.media_type = media_type
        self.caption = caption

    @classmethod
    def infer_media_details(cls, data:dict[str, any]):
        media_details = []

        try:
            if 'media' in data and bool(data['media']):
                if 'reddit_video' in data['media']:
                    media_details.append(('video', data['media']['reddit_video']['scrubber_media_url'], None))
                
                if 'oembed' in data['media'] and 'url' in data:
                    media_details.append(('video', data['url'], data['media']['oembed']['title']))

            if 'gallery_data' in data and 'media_metadata' in data:
                for media, description in zip(data['media_metadata'], data['gallery_data']['items']):
                    caption = description.get('caption', None)
                    media_details.append(('image', cls._decode_url(data['media_metadata'][media]['s']['u']), caption))
            
            elif 'media_metadata' in data:
                for media in data['media_metadata']:
                    if data['media_metadata'][media]['e'] == "AnimatedImage":
                        media_details.append(('gif', cls._decode_url(data['media_metadata'][media]['s']['gif']), None))
                    elif data['media_metadata'][media]['e'] == "Image":
                        media_details.append(('image', cls._decode_url(data['media_metadata'][media]['s']['u']), None))
        except KeyError as e:
            print(f"Erro ao processar dados. Chave ausente: {e}")
        except Exception as e:
            print(f"Erro ao processar dados: {e}")

        return media_details

    @classmethod
    def _decode_url(cls, url: str) -> str:
        return url.replace('&amp;', '&')
        
    @classmethod
    def from_json(cls, data:dict[str, any]) -> list:

        media_details = cls.infer_media_details(data)
        media = []
        for media_type, media_url, caption in media_details:
            media.append(cls(data['id'], media_url, media_type, caption))

        if not media:
            return None
                
        return media
