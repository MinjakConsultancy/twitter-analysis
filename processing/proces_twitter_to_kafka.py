import os
import logging
import configparser
import requests
import json
import yaml
from json import dumps
from kafka import KafkaProducer
from time import sleep
from requests.exceptions import ChunkedEncodingError

def get_rule(name, keywords):
    keyword_concat = ' OR '.join(keywords)
    keyword_concat = str(keyword_concat).strip(' OR ')
    print(keyword_concat)
    rule = {"value": "("+keyword_concat+") lang:nl", "tag": ""+name+""}
    return rule
    
class BearerTokenAuth(requests.auth.AuthBase):
    token = ''
    """
    Request an OAuth2 Bearer Token from Twitter
    """
    def __init__(self, bearer_token_url, consumer_key, consumer_secret):
        self.bearer_token_url = bearer_token_url
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        #self.bearer_token = self.get_bearer_token()
        self.token = self.get_bearer_token()
        #logging.info(self.token)
 
    def get_token(self):
        return self.token

    def get_bearer_token(self):
        logging.info(self.token)
        if self.token == '':
            logging.info("set token")
            response = requests.post(
                url = self.bearer_token_url,
                auth = (self.consumer_key, self.consumer_secret),
                data = { "grant_type": "client_credentials" },
                headers = { "User-Agent": "TwitterDevSampledStreamQuickStartPython" }
            )

            if response.status_code != 200:
                raise Exception("Cannot get a bearer token (HTTP {}): {}"
                    .format(response.status_code, response.text))
            body = response.json()
            logging.info(body['access_token'])
            os.environ["BEARER_TOKEN"]=body['access_token']
            self.token = body['access_token']
        return self.token


class Streamer(KafkaProducer):
    def __init__(self, topic, *args, **kwargs):
        self.topic = topic
        super().__init__(*args, **kwargs)

    def produce(self, stream_url, params, bearer_token):
        logging.info("produce start")
        self.get_stream( self.headers, self.set, self.bearer_token )
        # time.sleep(5) 
        # logging.info("timerEnd")


    def create_headers(self, bearer_token):
        headers = {"Authorization": "Bearer {}".format(bearer_token)}
        return headers

    def get_rules(self, headers, bearer_token):
        response = requests.get(
            "https://api.twitter.com/2/tweets/search/stream/rules", headers=headers
        )
        if response.status_code != 200:
            raise Exception(
                "Cannot get rules (HTTP {}): {}".format(response.status_code, response.text)
            )
        print(json.dumps(response.json()))
        return response.json()


    def delete_all_rules(self, headers, bearer_token, rules):
        if rules is None or "data" not in rules:
            return None

        ids = list(map(lambda rule: rule["id"], rules["data"]))
        payload = {"delete": {"ids": ids}}
        response = requests.post(
            "https://api.twitter.com/2/tweets/search/stream/rules",
            headers=headers,
            json=payload
        )
        if response.status_code != 200:
            raise Exception(
                "Cannot delete rules (HTTP {}): {}".format(
                    response.status_code, response.text
                )
            )
        print(json.dumps(response.json())) 

    def set_rules(self, headers, delete, bearer_token, rules):
        payload = {"add": rules}
        response = requests.post(
            "https://api.twitter.com/2/tweets/search/stream/rules",
            headers=headers,
            json=payload,
        )
        if response.status_code != 201:
            raise Exception(
                "Cannot add rules (HTTP {}): {}".format(response.status_code, response.text)
            )
        print(json.dumps(response.json()))

    def stream(self): #, headers, set, bearer_token):
        PARAMS = { 'tweet.fields': 'attachments,author_id,created_at,entities,geo,in_reply_to_user_id,lang,possibly_sensitive,referenced_tweets,source,public_metrics,withheld'} 
        response = requests.get(
            "https://api.twitter.com/2/tweets/search/stream", headers=self.headers, stream=True, params=PARAMS
        )
        try:
            print(response.status_code)
            if response.status_code != 200:
                raise Exception(
                    "Cannot get stream (HTTP {}): {}".format(
                        response.status_code, response.text
                    )
                )

            for response_line in response.iter_lines():
                if response_line:
                    json_response = json.loads(response_line)
                    #print(json.dumps(json_response, indent=4, sort_keys=True))
                    #push tweet to kafka
                    self.send(
                        self.topic,
                        json_response
                    )

                    logging.info("Queued tweet '{}'.".format(json_response['data']['id']))
                    # logging.info(self.metrics())
        except ChunkedEncodingError as e:
            response.close()   
            self.stream()         
        except (KeyboardInterrupt, SystemExit):
            response.close()
            raise

    def prepareStream(self, bearer_token, rules):
        #bearer_token = os.environ.get("BEARER_TOKEN")
        #logging.info(bearer_token.get_token())
        self.headers = self.create_headers( bearer_token.get_token() )
        #logging.info(headers)
        self.rules = self.get_rules( self.headers, bearer_token )
        self.delete = self.delete_all_rules( self.headers, bearer_token, self.rules)
        self.set = self.set_rules( self.headers, self.delete, bearer_token, rules )
        #self.get_stream( headers, set, bearer_token )

    




if __name__ == "__main__":
    # Load-up config file
    if os.environ.get('CONFIG_DIR') is None:
        ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
        ROOT_DIR = os.path.join(ROOT_DIR[0: ROOT_DIR.rfind('/')], "config")
    else:
        ROOT_DIR = os.environ.get('CONFIG_DIR')
    CONFIG_PATH = os.path.join(ROOT_DIR, 'config.ini')
    SECRET_PATH = os.path.join(ROOT_DIR, 'secret.ini')
    TWITTERCONFIG_PATH = os.path.join(ROOT_DIR, 'twitter-rules.yaml')

    yaml_content = yaml.load(open(TWITTERCONFIG_PATH, 'r'))
    rules = []
    for key, value in yaml_content.items():
        rules.append(get_rule(key, value))
    
    config = configparser.ConfigParser(strict=True)
    config.read_file(open(CONFIG_PATH, 'r'))
    config.read_file(open(SECRET_PATH, 'r'))

    # Setup logging
    logging.basicConfig(
        level = logging.INFO,
        format = "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")

    # Read config paramaters
    bearer_token_url    = config['twitter'].get('bearer_token_url').encode()
    stream_url          = config['twitter'].get('stream_url').encode()
    consumer_key        = config['twitter'].get('key').encode()
    consumer_secret     = config['twitter'].get('secret').encode()
    broker              = config['kafka'].get('broker')
    topic               = config['kafka'].get('topic')

    try:
        # Access Twitter's auth API to obtain a bearer token
        bearer_token = BearerTokenAuth(bearer_token_url, consumer_key, consumer_secret)
        bearer_token.get_bearer_token()

        streamer = Streamer( bootstrap_servers = broker,
                             value_serializer = lambda x: dumps(x).encode('utf-8'),
                             topic = topic
                           )    

        streamer.prepareStream(bearer_token, rules)
        streamer.stream()
           
        logging.info("Twitter API credentials parsed.")
    except KeyError as e:
        logging.error("Secret file not found. Make sure it is available in the directory.")
        exit()
    # except AttributeError as e:
    #     logging.error("Cannot read Twitter API credentials. Make sure that API key and secret are in the secret.ini file (also check spelling).")
    #     exit()




