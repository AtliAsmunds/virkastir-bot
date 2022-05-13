from typing import Dict, List, Tuple, DefaultDict
from facebook_scraper import get_posts
from collections import defaultdict
import datetime
from dotenv import load_dotenv
import os

class NoDataError(Exception):
    pass

class User:

    def __init__(self, id: str, name: str) -> None:
        self.id = id
        self.name = name
        self._comments: List[str, Dict[str, str]] | None = None

class CommentScraper:

    COMMENTS = "comments"
    NAME = "name"
    TYPES = ["comment", "reply"]
    NUMBER = "comment_number"

    def __init__(self,
                config: Dict[str, List[str]],
                commenter_data:DefaultDict[str, DefaultDict[str, List]] = defaultdict(lambda: defaultdict(list)),
                fb_user: str | None = None,
                fb_pass: str | None = None
                ) -> None:
        self._commenters = commenter_data
        self._spam = config["spam"]
        self._sources = config["sources"]   
        self._sorted_by_comments: List[str, DefaultDict] | None = None

        load_dotenv()
        self.user = os.getenv('FB_USER') if not fb_user else fb_user
        print(self.user)
        self.password = os.getenv('FB_PASSWORD') if not fb_pass else fb_pass

        if not self.user:
            raise ValueError("Missing value for fb_user. Set .env variable FB_USER or pass in a valid facebook username.")
        if not self.password:
            raise ValueError("Missing value for fb_pass. Set .env variable FB_PASSWORD or pass in a valid password.")

    def get_nr_comments(self) -> int:
        if not self._sorted_by_comments:
            raise NoDataError('No comments have been scraped. Use the scrape() method first.')
        return sum(comment[CommentScraper.NUMBER] for id, comment in self._sorted_by_comments)
    
    def get_top_commenters(self, top: int =10) -> List[Tuple[str, DefaultDict]]:
        nr_commenters = len(self._sorted_by_comments)
        if not self._sorted_by_comments:
            raise NoDataError('No comments have been scraped. Use the scrape() method first.')
        if nr_commenters < top:
            raise IndexError(f'Commenter count of {nr_commenters}, is less than the chosen number of {top}' )
        if top < 1:
            raise IndexError('Invalid index')
        
        return self._sorted_by_comments[:top]
        

    def scrape(self, sources: List[str] | None = None, days_back=1) -> None:
        posts = self._get_latest_news(
            self._sources if not sources else sources, # Use default sources if none are given
            days_back
        )

        for post in posts:
            comments = post["comments_full"]
            self._get_comments(comments)
        
        self._sorted_by_comments = sorted(self._commenters.items(), key=lambda item: item[1][CommentScraper.NUMBER], reverse=True)


    def _get_latest_news(self, sources: list, days_back=1) -> List:
        latest = []
        stop_time = datetime.datetime.now() - datetime.timedelta(days=days_back)
        for source in sources:
            print("Collecting comments from", source)
            for post in get_posts(
                source, pages=40, credentials=(self.user, self.password), options={"comments": True, "replies": True}
            ):
                if post["time"] < stop_time:
                    break
                else:
                    latest.append(post)
        return latest


    def _get_comments(self, comments, is_reply=False) -> None:
        for comment in comments:
            commenter_id = comment["commenter_id"]
            if commenter_id in self._spam:
                continue
            self._commenters[commenter_id][CommentScraper.NAME] = comment[ "commenter_name"]
            self._commenters[commenter_id][CommentScraper.COMMENTS].append(
                {
                    "text": comment["comment_text"],
                    "type": CommentScraper.TYPES[1]
                                if is_reply
                                else CommentScraper.TYPES[0],
                    "id": comment["comment_id"],
                }
            )
            try:
                self._commenters[commenter_id][CommentScraper.NUMBER] += 1
            except TypeError:
                self._commenters[commenter_id][CommentScraper.NUMBER] = 1

            try:
                if comment["replies"]:
                    self._get_comments(comment["replies"], is_reply=True)
            except KeyError:
                continue

if __name__ == "__main__":
    from pprint import pprint

    settings = {
       'spam': [],
       'sources': ['RUVfrettir']
    }

    scraper = CommentScraper(settings)
    scraper.scrape()
    print(scraper.get_nr_comments())
    for id, commenter in scraper.get_top_commenters():
        print(commenter[CommentScraper.NAME], commenter[CommentScraper.NUMBER])
        