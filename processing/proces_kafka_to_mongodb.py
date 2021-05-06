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
        super().__init__(*args, **kwargs)

    def process(self):
        try:
            self._teller = self._teller + 1
            if self._teller % 1000 == 0:
                logging.info(self._teller)

            message = self.__next__()
            message = json.loads(message.value)

            client = MongoClient(
                self._mongodb_url, username=self._mongodb_username, password=self._mongodb_password)
            tweetCollection = client.tweet.tweet
            wordCollection = client.tweet.word

            if 'data' in message:
                query = {
                    'data.id': {
                        '$eq': message['data']['id']
                    }
                }
                tweetCollection.find_one_and_replace(
                    filter=query, replacement=message, upsert=True)

            if 'word' in message:
                wordQuery = {
                    'word': {'$eq': message['word'].lower()},
                    'pos': {'$eq': message['pos']}
                }
                doc = wordCollection.find_one_and_update(wordQuery,
                                                         {"$inc": {"count": 1}}, upsert=True, return_document=ReturnDocument.AFTER)
                tags = message['tag']
                # tags.split('|')
                doc['tag'] = tags.split('|')
                if 'example-tweet' in message:
                    doc['example-tweet'] = message['example-tweet']
                wordCollection.find_and_modify(wordQuery, doc)
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
    processed_tweet_topic = config['kafka'].get('processed_tweet_topic')
    mongo_url = config['mongo'].get('url')
    mongo_username = config['mongo'].get('username')
    mongo_password = config['mongo'].get('password')
    logging.info(mongo_url)

    processor = Processor(processed_tweet_topic,   # Kafka topic
                          bootstrap_servers=broker,
                          enable_auto_commit=True,
                          auto_offset_reset='latest',
                          mongo_url=mongo_url,
                          mongo_username=mongo_username,
                          mongo_password=mongo_password,
                          group_id="mongo_consumergroup"
                          )
    while True:
        try:
            processor.process()
        except KeyboardInterrupt:
            processor.close()
            logging.info("Consumer closed. Bye!")
            exit(0)
