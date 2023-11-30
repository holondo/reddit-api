import mimetypes
import os
from urllib.parse import urlparse


def get_filename_from_url(url):
    parsed_url = urlparse(url)
    return os.path.basename(parsed_url.path)


class Media:
    def __init__(self, parent_id, post_id, media_url, media_type, caption=None):
        self.post_id: str = post_id
        self.media_url: str = media_url
        self.media_type: str = media_type
        self.caption: str | None = caption
        self.parent_id: str = parent_id

    def to_dict(self):
        return {
            "post_id": self.post_id,
            "media_url": self.media_url,
            "media_type": self.media_type,
            "caption": self.caption,
            "parent_id": self.parent_id,
            "filename": self.infer_filename(),
            "mime_type": self.infer_mime_type(),
            "extension": self.infer_extension(),
        }

    def infer_filename(self):
        try:
            return get_filename_from_url(self.media_url)
        except:
            return None

    def infer_mime_type(self):
        try:
            return mimetypes.guess_type(self.infer_filename())[0]
        except:
            return None

    def infer_extension(self):
        try:
            return mimetypes.guess_extension(self.infer_mime_type())
        except:
            return None

    @classmethod
    def infer_media_details(cls, data: dict[str, any]):
        media_details = []

        try:
            if "media" in data and bool(data["media"]):
                if "reddit_video" in data["media"]:
                    media_details.append(
                        (
                            "video",
                            # data["media"]["reddit_video"]["scrubber_media_url"],
                            data["media"]["reddit_video"]["fallback_url"],
                            "",
                        )
                    )

                if "oembed" in data["media"] and "url" in data:
                    media_details.append(
                        ("video", data["url"], data["media"]["oembed"]["title"])
                    )

            if "gallery_data" in data and "media_metadata" in data:
                for media, description in zip(
                    data["media_metadata"], data["gallery_data"]["items"]
                ):
                    caption = description.get("caption", "")
                    media_details.append(
                        (
                            "image",
                            cls._decode_url(data["media_metadata"][media]["s"]["u"]),
                            caption,
                        )
                    )

            elif "media_metadata" in data:
                for media in data["media_metadata"]:
                    if data["media_metadata"][media]["e"] == "AnimatedImage":
                        media_details.append(
                            (
                                "gif",
                                cls._decode_url(
                                    data["media_metadata"][media]["s"]["gif"]
                                ),
                                "",
                            )
                        )
                    elif data["media_metadata"][media]["e"] == "Image":
                        media_details.append(
                            (
                                "image",
                                cls._decode_url(
                                    data["media_metadata"][media]["s"]["u"]
                                ),
                                "",
                            )
                        )

            elif "url" in data:
                url = data.get("url", "")
                if url.endswith(".jpg") or url.endswith(".png"):
                    media_details.append(("image", url, ""))
                elif url.endswith(".gif"):
                    media_details.append(("gif", url, ""))
                elif url.endswith(".mp4"):
                    media_details.append(("video", url, ""))

        except KeyError as e:
            print(f"Erro ao processar dados. Chave ausente: {e}")
        except Exception as e:
            print(f"Erro ao processar dados: {e}")

        return media_details

    @classmethod
    def _decode_url(cls, url: str) -> str:
        return url.replace("&amp;", "&")

    @classmethod
    def from_json(cls, data: dict[str, any], parent_id) -> list:
        media_details = cls.infer_media_details(data)
        media = []
        for media_type, media_url, caption in media_details:
            media.append(cls(parent_id, data["id"], media_url, media_type, caption))

        return media
