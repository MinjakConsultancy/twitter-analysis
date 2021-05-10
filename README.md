# twitter-analysis

Project to gain some knowledge from docker, machinelearning and other fun stuff

## Introduction

This project is created as an educational project. Main goal is to get acquainted to new technologies.

## Architecture

![Architecture](./documentation/start-architecture.png)

Main goal is to visualize the trend of sentiment of tweets. As I am a native dutch speaker this is done in the context of the Dutch language.

As you can see in the picture we will try to catch some tweets in kakfa which will act as an buffer to do some processing. Processing consists of two parts. One is splitting tweets in words, saving the words to [MongoDB](https://www.mongodb.com/). Splitting the words is done with help of [Spacy](https://spacy.io/). On top of the MongoDB there is a small angular application where the sentiment of the words can be specified. 
The second part is determining the sentiment of the tweet. Based on the sentiment of words, te sentiment is estimated. There are loads of other (and far better) ways of determining the sentiment of tweets.
The sentiment is reported into an [elasticsearch](https://www.elastic.co) cluster and reported in a kibana dashboard. 
Neo4J is introduced as a next step and not actually used at the moment.

In this picture, the blue parts are docker-containers based on python. The yellow parts are based on nodejs.

## Deployment

All components should be delivered as docker-containers. In order to use a single IP to connect to all endpoints, NGINX (https://www.nginx.com/) is used as a reverse proxy.

## Configuration and Running 

To run this project, docker and docker-compose are required. 
Next to that the processing part of this project makes use of two configuration files, which the docker-compose file expects to be in the directory named config. "config.ini" and "secrets.ini". As a sample there are two files which you hae to rename and specify some connection details.
The rules, which configures what tweets should be processed, can be configured in the twitter-rules.yml.
The database connection for the backend-container is defined in ./backend/app/config/db.config.js


To retrieve a twitter key and secret, [this](https://support.yapsody.com/hc/en-us/articles/360003291573-How-do-I-get-a-Twitter-Consumer-Key-and-Consumer-Secret-key-#:~:text=How%20do%20I%20get%20a%20Twitter%20Consumer%20Key%20and%20Consumer%20Secret%20key%3F,-Ralph&text=Go%20to%20the%20API%20Keys,the%20screen%20into%20our%20application.) link should get you up to speed.


To startup the project it is nescesarry to first start the infra to prevent timeout-exceptions.
This can be done by  

```

docker-compose up -d kafka1 kafka2 kafka3 mongodb kibana neo4j

```

After a while startup the rest of the compose

```

docker-compose up -d 

```

Added a mongodb-collection with some words caught during development. To import them execute the following:

```
docker cp ./documentation/words.json twitter_infra_mongodb:/. 
docker cp ./documentation/tweets.json twitter_infra_mongodb:/. 

docker exec -it twitter_infra_mongodb mongoimport --username=root --password=example --uri='mongodb://root:example@localhost:27017/?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&ssl=false' -d tweet -c word --file=words.json
docker exec -it twitter_infra_mongodb mongoimport --username=root --password=example --uri='mongodb://root:example@localhost:27017/?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&ssl=false' -d tweet -c word --file=tweets.json
```

To export a new collection of tweets and words
```
docker exec -it twitter_infra_mongodb mongoexport --username=root --password=example --uri='mongodb://root:example@localhost:27017/?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&ssl=false' -d tweet -c word --file words.json
docker exec -it twitter_infra_mongodb mongoexport --username=root --password=example --uri='mongodb://root:example@localhost:27017/?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&ssl=false' -d tweet -c tweet --file tweets.json
docker cp  twitter_infra_mongodb:/words.json ./documentation/.
docker cp  twitter_infra_mongodb:/tweets.json ./documentation/.

```

