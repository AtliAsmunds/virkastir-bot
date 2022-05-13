from dotenv import load_dotenv
from utils.fb_scraper import CommentScraper
import os
import json
import tweepy

BASEDIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_FILE = os.path.join(BASEDIR, 'utils', 'scrape_config.json')

load_dotenv()
consumer_key = os.getenv('TWITTER_API')
consumer_secret = os.getenv('TWITTER_SECRET_API')
access_key = os.getenv('TWITTER_ACCESS')
access_secret = os.getenv('TWITTER_SECRET_ACCESS')

client = tweepy.Client(consumer_key=consumer_key, consumer_secret=consumer_secret, access_token=access_key, access_token_secret=access_secret)

with open(CONFIG_FILE) as f:
    config = json.load(f) 

scraper = CommentScraper(config)
scraper.scrape()
