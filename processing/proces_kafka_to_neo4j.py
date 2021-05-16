import configparser
import json
import logging
import os
from json import dumps, loads
from time import sleep

from kafka import KafkaConsumer 
from neo4j import GraphDatabase


class Processor(KafkaConsumer):
    def __init__(self, *args, **kwargs):
        self._broker  = kwargs['bootstrap_servers']
        self._neo4jDriver = GraphDatabase.driver(kwargs.pop('neo4j_uri', None)
                                                 , auth=(kwargs.pop('neo4j_username', None)
                                                         , kwargs.pop('neo4j_password', None)
                                                         )
                                                 ) 
        
        self.session = self._neo4jDriver.session()

        # Add uniqueness constraints
        try:
            self.session.run( "CREATE CONSTRAINT ON (t:Tweet) ASSERT t.id IS UNIQUE;")
            self.session.run( "CREATE CONSTRAINT ON (u:User) ASSERT u.screen_name IS UNIQUE;")
            self.session.run( "CREATE CONSTRAINT ON (h:Hashtag) ASSERT h.name IS UNIQUE;")
            self.session.run( "CREATE CONSTRAINT ON (l:Link) ASSERT l.url IS UNIQUE;")
            self.session.run( "CREATE CONSTRAINT ON (s:Source) ASSERT s.name IS UNIQUE;")
        except Exception as e:
            print("already init db")
            print(e.with_traceback)
        print('init ready')
        self._teller = 0
        super().__init__(*args, **kwargs)

    def save_tweet(self, tweet):
        
        if 'data' in tweet:
            if 'author_id' in tweet["data"].keys():
                # Pass dict to Cypher and build query.
                query = """
                UNWIND $tweets AS t
                WITH t
                ORDER BY t.id
                WITH t.data as t,
                    t.data.entities AS e,
                    t.data.user AS u,
                    t.data.retweeted_status AS retweet
                MERGE (tweet:Tweet {id:t.id})
                SET tweet.text = t.text,
                    tweet.created_at = t.created_at,
                    tweet.favorites = t.favorite_count
                MERGE (user:User {id:t.author_id})
                SET user.name = u.name,
                    user.location = u.location,
                    user.followers = u.followers_count,
                    user.following = u.friends_count,
                    user.statuses = u.statusus_count,
                    user.profile_image_url = u.profile_image_url
                FOREACH (h IN e.hashtags |
                MERGE (tag:Hashtag {name:h.tag})
                MERGE (tag)-[:TAGS]->(tweet)
                )
                FOREACH (h IN e.mentions |
                MERGE (mention:Mention {name:h.username})
                MERGE (mention)-[:MENTIONS]->(tweet)
                )
                FOREACH (h IN e.matching_rules |
                MERGE (rule:Rule {name:h.tag})
                MERGE (rule)-[:MATCHES]->(tweet)
                )
                MERGE (user)-[:POSTS]->(tweet)
                MERGE (source:Source {name:t.source})
                MERGE (tweet)-[:USING]->(source)
                """
                self.session.run(query,{'tweets':[tweet]})
            else:
                print(tweet)
        else:
            print(tweet)
        # except:
        #     print('err')
        
        
        
    def save_greeting(self, message):
        with self._neo4jDriver.session() as session:
            greeting = session.write_transaction(self._create_and_return_greeting, message)
            print(greeting)

    def process(self):
        try:
            
            message = self.__next__()
            message = json.loads(message.value)
            self.save_tweet(message)
            self._teller = self._teller +1
            if self._teller % 100 == 0:
                logging.warn(self._teller)
                
            #res = self._es.index(index=self._elastic_index, body=message)
            logging.debug('created neo4j')
            return     
        except StopIteration as e:
            logging.warning("No incoming message found at Kafka broker: {}.".format(self.broker))
            return
        except ConnectionError as e:
            logging.warning("Unable to connect to InfluxDB. Continuing ...")
            return

if __name__ == "__main__":
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
        level = logging.WARNING,
        format = "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")

    # Read config paramaters
    broker          = config['kafka'].get('broker')
    enriched_tweet_topic = config['kafka'].get('enriched_tweet_topic')
    neo4j_username   = config['neo4j'].get('username')
    neo4j_password   = config['neo4j'].get('password')
    neo4j_uri     = config['neo4j'].get('uri')
    kafka_consumergroup_id = config['neo4j'].get('kafka-consumergroup-id')

 
    processor = Processor(  enriched_tweet_topic,   # Kafka topic
                            bootstrap_servers = broker,
                            enable_auto_commit = True,
                            auto_offset_reset = 'latest',
                            group_id = kafka_consumergroup_id,
                            neo4j_uri = neo4j_uri,
                            neo4j_username = neo4j_username,
                            neo4j_password = neo4j_password
                        )    
    while True:
        try:
            processor.process()
        except KeyboardInterrupt:
            processor.close()
            logging.info("Consumer closed. Bye!")
            exit(0)
