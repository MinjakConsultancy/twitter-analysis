import os
import logging
import configparser
import json
from json import dumps
from time import sleep
from datetime import datetime, timezone
from kafka import SimpleProducer, KafkaClient
from json import loads
import spacy
from spacy.lang.nl import Dutch
from pymongo import MongoClient
import datetime


class Processor():
    def __init__(self, *args, **kwargs):

        self._broker = kwargs['bootstrap_servers']
        self._twitter_topic = kwargs.pop('topic', None)
        self._processed_topic = kwargs.pop('processed_tweet_topic', None)
        self._word_topic = kwargs.pop('word_topic', None)
        self._kafka = KafkaClient(self._broker)
        self._producer = SimpleProducer(self._kafka)
        
        self._mongodb_url = kwargs.pop('mongo_url', None)
        self._mongodb_username = kwargs.pop('mongo_username', None)
        self._mongodb_password = kwargs.pop('mongo_password', None)
        self._mongoclient = MongoClient(
                self._mongodb_url, username=self._mongodb_username, password=self._mongodb_password)
        self._tweetCollection = self._mongoclient.tweet.tweet

        self._number_of_tweets = kwargs['number_of_tweets']

    def process(self):
        teller =0
        for tweet in self._tweetCollection.find( no_cursor_timeout=True).limit(self._number_of_tweets):#.sort([("data.created_at",-1)], allowDiskUse=True):
            teller = teller +1
            if teller % (self._number_of_tweets/10) == 0:
                print(teller)
            #tweet["data"]['text'] = 'test romano herhaling: '+str(tweet["data"]['text'])
            del tweet["_id"]
            del tweet["spacy"]
            #print(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]+'Z')
            tweet["data"]["created_at"]=datetime.datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-6]+'000Z'
            self._producer.send_messages(self._twitter_topic, json.dumps(tweet).encode('utf-8'))
        return

if __name__ == "__main__":
    if os.environ.get('CONFIG_DIR') is None:
        ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
        ROOT_DIR = ROOT_DIR[0: ROOT_DIR.rfind('/')]+"/config/"
    else:
        ROOT_DIR = os.environ.get('CONFIG_DIR')
    
    NUMBER_OF_TWEETS_REPLAYED = 100
    if 'NUMBER_OF_TWEETS_REPLAYED' in os.environ.keys():
        NUMBER_OF_TWEETS_REPLAYED = int( os.environ.get('NUMBER_OF_TWEETS_REPLAYED'))
        
    CONFIG_PATH = os.path.join(ROOT_DIR, 'config.ini')
    SECRET_PATH = os.path.join(ROOT_DIR, 'secret.ini')

    config = configparser.ConfigParser(strict=True)
    config.read_file(open(CONFIG_PATH, 'r'))
    config.read_file(open(SECRET_PATH, 'r'))

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")

    # Read config paramaters
    broker = config['kafka'].get('broker')
    topic = config['kafka'].get('topic')
    processed_tweet_topic = config['kafka'].get('processed_tweet_topic')
    word_topic = config['kafka'].get('word_topic')
    mongo_url = config['mongo'].get('url')
    mongo_username = config['mongo'].get('username')
    mongo_password = config['mongo'].get('password')

    # try:
    processor = Processor(topic=topic,   
                          bootstrap_servers=broker,
                          enable_auto_commit=True,
                          auto_offset_reset='latest',
                          processed_tweet_topic=processed_tweet_topic,
                          word_topic=word_topic,
                          mongo_url=mongo_url,
                          mongo_username=mongo_username,
                          mongo_password=mongo_password,
                          group_id="processing_consumergroup",
                          number_of_tweets=NUMBER_OF_TWEETS_REPLAYED,
                          )
    while True:
        try:
            processor.process()
            exit(0)
        except KeyboardInterrupt:
            processor.close()
            logging.info("Consumer closed. Bye!")
            exit(0)
