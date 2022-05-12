from typing import Dict, List
from facebook_scraper import get_posts
import json
from collections import defaultdict
import datetime

class NoDataError(Exception):
    pass


class CommentScraper:

    COMMENTS = "comments"
    NAME = "name"
    TYPES = ["comment", "reply"]
    NUMBER = "comment_number"

    def __init__(self, config: Dict[str, List[str]]) -> None:
        self.commenters = defaultdict(lambda: defaultdict(list))
        self.spam = config["spam"]
        self.sources = config["sources"]

    def get_nr_comments(self) -> int:
        pass

    def scrape(self, sources: List[str] | None = None, days_back=1):
        posts = self._get_latest_news(
            self.sources if not sources else sources, 
            days_back
        )

        for post in posts:
            comments = post["comments_full"]
            self._get_comments(post)


    def _get_latest_news(self, sources: list, days_back=1):
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


    def _get_comments(self, post, is_reply=False):
        for comment in post:
            commenter_id = comment["commenter_id"]
            if commenter_id in self.spam:
                continue
            self.commenters[commenter_id][CommentScraper.NAME] = comment[ "commenter_name"]
            self.commenters[commenter_id][CommentScraper.COMMENTS].append(
                {
                    "text": comment["comment_text"],
                    "type": CommentScraper.TYPES[1]
                                if is_reply
                                else CommentScraper.TYPES[0],
                    "id": comment["comment_id"],
                }
            )
            try:
                self.commenters[commenter_id][CommentScraper.NUMBER] += 1
            except TypeError:
                self.commenters[commenter_id][CommentScraper.NUMBER] = 1

            try:
                if comment["replies"]:
                    self._get_comments(comment["replies"], is_reply=True)
            except KeyError:
                continue