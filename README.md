# twitter-analysis

Project to gain some knowledge from docker, machinelearning and other fun stuff

## Introduction

This project is created as an educational project. Main goal is to get acquainted to new technologies.

## Architecture

![Architecture](./documentation/start-architecture.png)

Main goal is to visualize the trend of sentiment of tweets. As I am a native dutch speaker this is done in the context of the Dutch language.

As you can see in the picture we will try to catch some tweets in kakfa which will act as an buffer to do some processing. Processing consists of two parts. One is splitting tweets in words, saving the words to [MongoDB](https://www.mongodb.com/). Splitting the words is done with help of [Spacy](https://spacy.io/). On top of the MongoDB there is a small angular application where the sentiment of the words can be specified.
The second part is determining the sentiment of the tweet. Based on the sentiment of words, te sentiment is calculated. There are loads of other (and far better) ways of determining the sentiment of tweets but to make things not overly complex, this is fine for now.
The sentiment is reported into an [elasticsearch](https://www.elastic.co) cluster and reported in a kibana dashboard.
Neo4J is introduced as a next step and not actually used at the moment.

In this picture, the blue parts are docker-containers based on python. The yellow parts are based on nodejs.
All blue components share the same docker image. The nodejs containers are split in a frontend and a backend image.

## Deployment

All components should be delivered as docker-containers. In order to use a single IP to connect to all endpoints, [NGINX](https://www.nginx.com/) is used as a reverse proxy.

## Configuration and Running

To run this project, docker and docker-compose are required.
Next to that the processing part of this project makes use of two configuration files, which the docker-compose file expects to be in the directory named config. "config.ini" and "secrets.ini". As a sample there are two files which you hae to rename and specify some connection details.
The rules, which configures what tweets should be processed, can be configured in the twitter-rules.yml.
The database connection for the backend-container is defined in ./backend/app/config/db.config.js

To retrieve a twitter key and secret, [this](https://support.yapsody.com/hc/en-us/articles/360003291573-How-do-I-get-a-Twitter-Consumer-Key-and-Consumer-Secret-key-#:~:text=How%20do%20I%20get%20a%20Twitter%20Consumer%20Key%20and%20Consumer%20Secret%20key%3F,-Ralph&text=Go%20to%20the%20API%20Keys,the%20screen%20into%20our%20application.) link should get you up to speed.

To startup the project it is nescesarry to create a docker network and to start the infra-part to prevent timeout-exceptions.
Next we can create the topics in kafka, build the custom docker immages.

```linux

docker network create twitter-analysis-network
docker-compose up -d kafka1 kafka2 kafka3 mongodb kibana neo4j
docker-compose up kafka-setup
docker-compose build

```

After a while startup the rest of the functional-containers of the docker-compose

```linux

docker-compose up -d frontend \
kafka2kafka \
kafka2elastic_word \
kafka2elastic_tweet \
kafka2mongodb_word \
kafka2mongodb_tweet \
kafka2neo4j \
twitter2kafka

```

Added a mongodb-collection with some words caught during development. To import them execute the following:

```linux

docker cp ./documentation/words.json twitter_infra_mongodb:/. 
docker cp ./documentation/tweets.json twitter_infra_mongodb:/. 

docker exec -it twitter_infra_mongodb mongoimport --username=root --password=example --uri='mongodb://root:example@localhost:27017/?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&ssl=false' -d tweet -c word --file=words.json
docker exec -it twitter_infra_mongodb mongoimport --username=root --password=example --uri='mongodb://root:example@localhost:27017/?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&ssl=false' -d tweet -c tweet --file=tweets.json

```

To reset the wordcount in order to let new words popup in the frontend.

```linux

docker exec -it twitter_infra_mongodb mongo
# db = connect("mongodb://root:example@localhost:27017")
# use tweet
# db.word.updateMany({},{"$set": {"count":0}})
# exit

```

To export a new collection of tweets and words

```linux

docker exec -it twitter_infra_mongodb mongoexport --username=root --password=example --uri='mongodb://root:example@localhost:27017/?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&ssl=false' -d tweet -c word --out words.json

docker cp  twitter_infra_mongodb:/words.json ./documentation/.

docker exec -it twitter_infra_mongodb mongoexport --username=root --password=example --uri='mongodb://root:example@localhost:27017/?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&ssl=false' -d tweet -c tweet --out tweets.json

docker cp  twitter_infra_mongodb:/tweets.json ./documentation/.

```

It is also possible to "replay" twitter by running the replay_tweets container. This will replay a number of tweets (200) with the current date.

```linux

docker-compose up replay_tweets

```
