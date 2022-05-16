from typing import Dict, List, Tuple
from facebook_scraper import get_posts
import datetime
from dotenv import load_dotenv
import os

class NoDataError(Exception):
    pass

class User:

    def __init__(self, id: str, name: str) -> None:
        self.id = id
        self.name = name
        self._comments: Dict[str, Dict[str, str]] | None = {}
        self.nr_comments = 0
        self.nr_replies = 0
    
    def __str__(self) -> str:
        return str(self.name)
    
    def __len__(self) -> int:
        return self.nr_comments + self.nr_replies

    def add_comment(self, text: str, type: str, id: str):
        if not self._comments or id not in self._comments:
            if type == 'comment':
                self.nr_comments += 1
            else:
                self.nr_replies +=1

        self._comments[id] = {'text': text, 'type': type}
    
    def get_comments(self) -> List[Tuple[str, str]]:
        return [(comment['type'], comment['text']) for comment in self._comments.values() ]
    
    def generate_dict(self) -> Dict[str, str | int | Dict]:
        return {
            'name': self.name,
            'id': self.id,
            'nr_comments': self.nr_comments,
            'nr_replies': self.nr_replies,
            'total_nr_comments': self.nr_replies + self.nr_comments,
            'comments': self._comments
        }
class CommentScraper:

    COMMENTS = "comments"
    NAME = "name"
    TYPES = ["comment", "reply"]
    NUMBER = "comment_number"

    def __init__(self,
                config: Dict[str, List[str]],
                commenter_data:Dict[str, User] = {},
                fb_user: str | None = None,
                fb_pass: str | None = None
                ) -> None:
        self._commenters = commenter_data
        self._spam = config["spam"]
        self._sources = config["sources"]   
        self._sorted_by_comments: List[str, User] | None = None

        load_dotenv()
        self.user = os.getenv('FB_USER') if not fb_user else fb_user
        self.password = os.getenv('FB_PASSWORD') if not fb_pass else fb_pass

        if not self.user:
            print('No Facebook account accessed.')

    def get_nr_comments(self) -> int:
        if not self._commenters:
            raise NoDataError('No comments have been scraped. Use the scrape() method first.')
        
        return sum(len(user) for user in self._commenters.values())

    
    def get_top_commenters(self, top: int =10) -> List[User]:
        nr_commenters = len(self._sorted_by_comments)
        if not self._sorted_by_comments:
            raise NoDataError('No comments have been scraped. Use the scrape() method first.')
        if nr_commenters < top:
            raise IndexError(f'Commenter count of {nr_commenters}, is less than the chosen number of {top}' )
        if top < 1:
            raise IndexError('Invalid index')
        
        return self._sorted_by_comments[:top]
        
    def has_data(self) -> bool:
        return self.get_nr_comments() > 0

    def scrape(self, sources: List[str] | None = None, days_back=1) -> None:
        posts = self._get_latest_news(
            self._sources if not sources else sources, # Use default sources if none are given
            days_back
        )

        for post in posts:
            comments = post["comments_full"]
            self._get_comments(comments)
        
        self._sorted_by_comments = sorted(self._commenters.values(), key=lambda item:  len(item), reverse=True)


    def _get_latest_news(self, sources: list, days_back=1) -> List:
        posts = []
        stop_time = datetime.datetime.now() - datetime.timedelta(days=days_back)
        
        for source in sources:
            print("Collecting comments from", source)
            
            for post in get_posts(
                source,
                pages=40,
                credentials=(self.user, self.password) if self.user else None,
                options={"comments": True, "replies": True}
            ):
                if post["time"] < stop_time:
                    break
                else:
                    posts.append(post)
        return posts


    def _get_comments(self, comments, is_reply=False) -> None:
        for comment in comments:
            commenter_id = comment["commenter_id"]
            
            if commenter_id in self._spam:
                continue
            if commenter_id not in self._commenters:
                user = self._commenters[commenter_id] = User(commenter_id, comment['commenter_name'])
            else:
                user = self._commenters[commenter_id]

            user.add_comment(comment['comment_text'].replace('\n', ''),
                             'reply' if is_reply else 'comment',
                             comment['comment_id'])


            try:
                if comment["replies"]:
                    self._get_comments(comment["replies"], is_reply=True)
            except KeyError:
                continue


if __name__ == "__main__":
    from pprint import pprint
    from random import choice

    settings = {
       'spam': [],
       'sources': [    "RUVfrettir",
    "RUVohf",
    "www.dv.is",
    "visir.is",
    "Kjarninn",
    "stundin",
    "hringbraut",
    "Frettabladid",
    "mbl.is"]
    }

    scraper = CommentScraper(settings)
    scraper.scrape()
    print(scraper.get_nr_comments())
    for commenter in scraper.get_top_commenters():
        random_comment = choice(commenter.get_comments())
        print(f"{len(commenter)}\t{commenter}\t{random_comment[1]}")
        