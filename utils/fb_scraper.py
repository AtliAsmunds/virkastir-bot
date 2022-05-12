from typing import Dict, List, Tuple, DefaultDict
from facebook_scraper import get_posts
from collections import defaultdict
import datetime
from dotenv import load_dotenv
import os

class NoDataError(Exception):
    pass


class CommentScraper:

    COMMENTS = "comments"
    NAME = "name"
    TYPES = ["comment", "reply"]
    NUMBER = "comment_number"

    def __init__(self,
                config: Dict[str, List[str]],
                commenter_data:DefaultDict[str, DefaultDict[str, List]] = defaultdict(lambda: defaultdict(list))
                ) -> None:
        self._commenters = commenter_data
        self._spam = config["spam"]
        self._sources = config["sources"]   
        self._sorted_by_comments: List[str, DefaultDict] | None = None

        load_dotenv()
        self.user = os.getenv('USER')
        self.password = os.getenv('PASSWORD')

        if not self.user:
            raise KeyError("Environmental variable 'USER' not found in .env")
        if not self.password:
            raise KeyError("Environmental variable 'PASSWORD' not found in .env")

    def get_nr_comments(self) -> int:
        if not self._sorted_by_comments:
            raise NoDataError('No comments have been scraped. Use the scrape() method first.')
        return sum(comment[CommentScraper.NUMBER] for id, comment in self._sorted_by_comments)
    
    def get_top_commenters():
        pass

    def scrape(self, sources: List[str] | None = None, days_back=1) -> None:
        posts = self._get_latest_news(
            self._sources if not sources else sources, # Use default sources if none are given
            days_back
        )

        for post in posts:
            comments = post["comments_full"]
            self._get_comments(comments)
        
        self._sorted_by_comments = sorted(self._commenters.items(), key=lambda item: item[1][CommentScraper.NUMBER])


    def _get_latest_news(self, sources: list, days_back=1) -> List:
        latest = []
        stop_time = datetime.datetime.now() - datetime.timedelta(days=days_back)
        for source in sources:
            print("Collecting comments from", source)
            for post in get_posts(
                source, pages=40, options={"comments": True, "replies": True}
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
   settings = {
       'spam': [],
       'sources': ['RUVfrettir']
   }

   scraper = CommentScraper(settings)
   scraper.scrape()
   print(scraper.get_nr_comments())
