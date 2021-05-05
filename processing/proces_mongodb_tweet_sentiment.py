import os
import logging
import configparser
import json
import re
from json import dumps
from time import sleep
from kafka import KafkaConsumer
from kafka import SimpleProducer, KafkaClient
from pymongo import MongoClient, ReturnDocument
from json import loads
from string import punctuation
from kafka.errors import KafkaError


class Processor():
    def __init__(self, *args, **kwargs):
        
        self._teller = 0
        self._mongodb_url  = kwargs.pop('mongo_url', None)
        self._mongodb_username  = kwargs.pop('mongo_username', None)
        self._mongodb_password  = kwargs.pop('mongo_password', None)
        super().__init__(*args, **kwargs)

    def process(self):
        client = MongoClient(self._mongodb_url, username = self._mongodb_username, password = self._mongodb_password)
        tweetCollection = client.tweet.tweet
        wordCollection = client.tweet.word
        tweetCollection.update_many({}, {"$set": {"sentiment":0}})
        self._teller = self._teller +1

        if self._teller % 100 == 0:
            logging.info(self._teller)

        for doc in wordCollection.find({"$or":[{"sentiment":{"$lt":0}}
                                    ,{"sentiment":{"$gt":0}}
                                    ]}
                            ):
            logging.info(doc["word"])
            logging.info(doc["pos"])
            logging.info(doc["sentiment"])
            query = {
                'spacy.tokens': {
                    '$elemMatch': {
                        'word': doc["word"],
                        'pos': doc["pos"]
                    }
                }
            }
            tweetCollection.update_many( query
                                        , { "$inc" : {"sentiment": doc["sentiment"]}}
                                    )
        
        return
        
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level = logging.INFO,
        format = "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")

    # Load-up config file
    if os.environ.get('CONFIG_DIR') is None:
        ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
        ROOT_DIR = ROOT_DIR[0: ROOT_DIR.rfind('/')]+"/config/"
    else:
        ROOT_DIR = os.environ.get('CONFIG_DIR')
    CONFIG_PATH = os.path.join(ROOT_DIR, 'config.ini')
    SECRET_PATH = os.path.join(ROOT_DIR, 'secret.ini')

    config = configparser.ConfigParser(strict=True)
    config.read_file(open(CONFIG_PATH, 'r'))
    config.read_file(open(SECRET_PATH, 'r'))

    # Setup logging
    logging.basicConfig(
        level = logging.INFO,
        format = "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")

    mongo_url       = config['mongo'].get('url')
    mongo_username  = config['mongo'].get('username')
    mongo_password  = config['mongo'].get('password')
    logging.info(mongo_url)

    processor = Processor(  mongo_url = mongo_url,
                            mongo_username = mongo_username,
                            mongo_password = mongo_password,
                         )    
    try:
        processor.process()
    
    except KeyboardInterrupt:
        logging.info("Consumer closed. Bye!")
        exit(0)
        