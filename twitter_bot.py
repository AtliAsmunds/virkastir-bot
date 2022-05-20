from dotenv import load_dotenv
from utils.fb_scraper import CommentScraper, User
from random import sample
import os
import json
import tweepy

MAX_POST_LEN = 280
BASEDIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_FILE = os.path.join(BASEDIR, 'utils', 'scrape_config.json')

load_dotenv()
consumer_key = os.getenv('TWITTER_API')
consumer_secret = os.getenv('TWITTER_SECRET_API')
access_key = os.getenv('TWITTER_ACCESS')
access_secret = os.getenv('TWITTER_SECRET_ACCESS')

client = tweepy.Client(consumer_key=consumer_key, consumer_secret=consumer_secret, access_token=access_key, access_token_secret=access_secret)

COOKIES = os.path.join(BASEDIR, 'facebook.com_cookies.txt')


with open(CONFIG_FILE) as f:
    config = json.load(f) 

scraper = CommentScraper(config, cookies=COOKIES)
scraper.scrape()
top_commenter: User = scraper.get_top_commenters(top=1)[0]

text = f"Fjöldi athugasemda: {scraper.get_nr_comments()}\n\nVirkasti notandinn er {top_commenter} með {len(top_commenter)} comment/reply\n\n"

random_comments = sample(top_commenter.get_comments(), len(top_commenter))

for comment in random_comments:
    if len(comment[1]) + len(text) + 2 <= MAX_POST_LEN:
        text += f'"{comment[1]}"'
        break



client.create_tweet(text=text)