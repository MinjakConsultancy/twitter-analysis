import os
import logging
import configparser
import json
from json import dumps
from time import sleep
from kafka import KafkaConsumer
from kafka import SimpleProducer, KafkaClient
from json import loads
import spacy
from spacy.lang.nl import Dutch
from pymongo import MongoClient


class Processor(KafkaConsumer):
    def __init__(self, *args, **kwargs):

        # spacy
        self._nlp = spacy.load("nl_core_news_lg")
        self._nlp_nl = Dutch()

        self._broker = kwargs['bootstrap_servers']
        self._processed_topic = kwargs.pop('processed_tweet_topic', None)
        self._word_topic = kwargs.pop('word_topic', None)
        self._kafka = KafkaClient(self._broker)
        self._producer = SimpleProducer(self._kafka)
        
        self._mongodb_url = kwargs.pop('mongo_url', None)
        self._mongodb_username = kwargs.pop('mongo_username', None)
        self._mongodb_password = kwargs.pop('mongo_password', None)
        self._mongoclient = MongoClient(
                self._mongodb_url, username=self._mongodb_username, password=self._mongodb_password)
        self._wordCollection = self._mongoclient.tweet.word

        super().__init__(*args, **kwargs)

    @staticmethod
    def removeDuplicatesInArray(array):
        seen = set(array)
        result = []
        for item in array:
            if item not in result:
                result.append(item)
        return result

    def removeStringInArray(self, array, string):
        if string in array:
            array.remove(string)

    def process(self):
        try:
            message = self.__next__()
            message = json.loads(message.value)

            if 'data' in message:
                tweet_text = message['data']['text']
                doc = self._nlp(tweet_text)
                message['spacy'] = doc.to_json()
                sentiment = 0
                for token in message['spacy']['tokens']:
                    token['word'] = tweet_text[token['start']: token['end']]
                    token['example_tweet'] = tweet_text
                    self._producer.send_messages(
                        processed_tweet_topic, json.dumps(token).encode('utf-8'))
                    wordQuery = {
                        'word': {'$eq': token['word']},
                        'pos': {'$eq': token['pos']},
                        '$or': [{'sentiment': {'$lt': 0}}, {'sentiment': {'$gt': 0}}]
                    }
                    word = self._wordCollection.find_one(wordQuery)
                    if word != None:
                        sentiment += word['sentiment']
                message['sentiment'] = sentiment

                matching_rules = message.get('matching_rules')
                if matching_rules:
                    matching_rules2 = []
                    for matching_rule in matching_rules:
                        if str(matching_rule['tag']).endswith('/"'):
                            matching_rule['tag'] = matching_rule['tag'][:-1]
                        matching_rules2.append(matching_rule)
                    message['matching_rules'] = matching_rules2

                self._producer.send_messages(
                    processed_tweet_topic, json.dumps(message).encode('utf-8'))
                logging.info('tweet enriched')
            return

        except StopIteration as e:
            logging.warning(
                "No incoming message found at Kafka broker: {}.".format(self.broker))
            return

        except ConnectionError as e:
            logging.warning("Unable to connect to InfluxDB. Continuing ...")
            return


if __name__ == "__main__":
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
    topic = config['kafka'].get('topic')
    processed_tweet_topic = config['kafka'].get('processed_tweet_topic')
    word_topic = config['kafka'].get('word_topic')
    mongo_url = config['mongo'].get('url')
    mongo_username = config['mongo'].get('username')
    mongo_password = config['mongo'].get('password')

    # try:
    processor = Processor(topic,   # Kafka topic
                          bootstrap_servers=broker,
                          enable_auto_commit=True,
                          auto_offset_reset='latest',
                          #value_deserializer = lambda x: dumps(x).decode('utf-8'),
                          processed_tweet_topic=processed_tweet_topic,
                          word_topic=word_topic,
                          mongo_url=mongo_url,
                          mongo_username=mongo_username,
                          mongo_password=mongo_password,
                          group_id="processing_consumergroup"
                          )
    while True:
        try:
            processor.process()
            # processor.close()
            # exit(0)
        except KeyboardInterrupt:
            processor.close()
            logging.info("Consumer closed. Bye!")
            exit(0)
