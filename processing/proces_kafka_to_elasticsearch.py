import os
import logging
import configparser
import json
from json import dumps
from time import sleep
from kafka import KafkaConsumer
from json import loads
from elasticsearch import Elasticsearch


class Processor(KafkaConsumer):
    def __init__(self, *args, **kwargs):
        self._broker = kwargs['bootstrap_servers']
        self._elastic_index = kwargs.pop('elastic_index', None)
        self._elastic_url = kwargs.pop('elastic_url', None)
        logging.info(self._elastic_index)
        self._es = Elasticsearch(self._elastic_url)
        self._teller = 0
        super().__init__(*args, **kwargs)

    def process(self):
        try:
            message = self.__next__()
            message = json.loads(message.value)
            self._teller = self._teller + 1
            if self._teller % 100 == 0:
                logging.warn(self._teller)
            res = self._es.index(index=self._elastic_index, body=message)
            logging.debug('created elastic document')
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
        level=logging.WARNING,
        format="[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")

    # Read config paramaters
    broker = config['kafka'].get('broker')
    processed_tweet_topic = config['kafka'].get('processed_tweet_topic')
    elastic_index = config['elastic'].get('index')
    elastic_url = config['elastic'].get('url')
    print(elastic_url)
    processor = Processor(processed_tweet_topic,   # Kafka topic
                          bootstrap_servers=broker,
                          enable_auto_commit=True,
                          auto_offset_reset='latest',
                          group_id="elastic_consumergroup",
                          elastic_index=elastic_index,
                          elastic_url=elastic_url
                          )
    while True:
        try:
            processor.process()
        except KeyboardInterrupt:
            processor.close()
            logging.info("Consumer closed. Bye!")
            exit(0)
