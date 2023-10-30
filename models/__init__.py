try:
    from .subreddit import Subreddit
    from .post import Post
    from .comment import Comment
    from .media import Media
except ImportError:
    from subreddit import Subreddit
    from post import Post
    from comment import Comment
    from media import Media