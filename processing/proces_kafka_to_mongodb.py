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


class Processor(KafkaConsumer):
    def __init__(self, *args, **kwargs):

        self._teller = 0
        self._broker = kwargs['bootstrap_servers']
        kafka = KafkaClient(self._broker)
        self._producer = SimpleProducer(kafka)
        self._mongodb_url = kwargs.pop('mongo_url', None)
        self._mongodb_username = kwargs.pop('mongo_username', None)
        self._mongodb_password = kwargs.pop('mongo_password', None)
        self._tweet_or_word = kwargs.pop('tweet_or_word', "TWEET")
        super().__init__(*args, **kwargs)

    def process(self):
        try:            
            self._teller = self._teller + 1
            if self._teller % 1000 == 0:
                logging.info(self._teller)
            if self._tweet_or_word == "TWEET":
                message = self.__next__()
                message = json.loads(message.value)

                client = MongoClient(
                    self._mongodb_url, username=self._mongodb_username, password=self._mongodb_password)
                tweetCollection = client.tweet.tweet
                query = {
                    'data.id': {
                        '$eq': message['data']['id']
                    }
                }
                tweetCollection.find_one_and_replace(
                    filter=query, replacement=message, upsert=True)


            if self._tweet_or_word == "WORD":
                message = self.__next__()
                message = json.loads(message.value)

                client = MongoClient(
                    self._mongodb_url, username=self._mongodb_username, password=self._mongodb_password)
                wordCollection = client.tweet.word
                wordQuery = {
                    'word': {'$eq': message['word'].lower()},
                    'pos': {'$eq': message['pos']}
                }
                logging.debug(message)
                if 'example-tweet' in message:
                    doc = wordCollection.find_one_and_update(wordQuery,
                                                            { "$inc": { "count": 1}
                                                            , "$set": { "date_last_used": message['date_last_used']
                                                                    , "example-tweet" : message['example-tweet']
                                                                    }
                                                            }, upsert=True, return_document=ReturnDocument.AFTER)
                else:
                    doc = wordCollection.find_one_and_update(wordQuery,
                                                            { "$inc": { "count": 1}
                                                            , "$set": { "date_last_used": message['date_last_used']}
                                                            }, upsert=True, return_document=ReturnDocument.AFTER)
                                                                            
                tags = message['tag']
                # tags.split('|')
                doc['tag'] = tags.split('|')
 #               if 'example-tweet' in message:
 #                   doc['example-tweet'] = message['example-tweet']
 #               wordCollection.find_and_modify(wordQuery, doc)
                logging.debug('word merged: ' +
                              doc['word']+' - '+str(doc['count']))
            return

        except StopIteration as e:
            logging.warning(
                "No incoming message found at Kafka broker: {}.".format(self.broker))
            return

        except ConnectionError as e:
            logging.warning("Unable to connect to InfluxDB. Continuing ...")
            return


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")

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
        level=logging.INFO,
        format="[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")

    # Read config paramaters
    broker = config['kafka'].get('broker')
    enriched_tweet_topic = config['kafka'].get('enriched_tweet_topic')
    word_topic = config['kafka'].get('word_topic')
    mongo_url = config['mongo'].get('url')
    mongo_username = config['mongo'].get('username')
    mongo_password = config['mongo'].get('password')
    kafka_consumergroup_id = config['mongo'].get('kafka-consumergroup-id')
    logging.info(mongo_url)

    if os.environ.get('INDEX')=='TWEET':        
        processor = Processor(enriched_tweet_topic,   # Kafka topic
                            bootstrap_servers=broker,
                            enable_auto_commit=True,
                            auto_offset_reset='latest',
                            mongo_url=mongo_url,
                            mongo_username=mongo_username,
                            mongo_password=mongo_password,
                            group_id=kafka_consumergroup_id,
                            tweet_or_word = os.environ.get('INDEX')
                            )
    else:
        processor = Processor(word_topic,   # Kafka topic
                            bootstrap_servers=broker,
                            enable_auto_commit=True,
                            auto_offset_reset='latest',
                            mongo_url=mongo_url,
                            mongo_username=mongo_username,
                            mongo_password=mongo_password,
                            group_id=kafka_consumergroup_id,
                            tweet_or_word = os.environ.get('INDEX')
                            )
    while True:
        try:
            processor.process()
        except KeyboardInterrupt:
            processor.close()
            logging.info("Consumer closed. Bye!")
            exit(0)
