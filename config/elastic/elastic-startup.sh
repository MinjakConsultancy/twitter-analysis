#!/bin/sh


curl -XDELETE "http://elastic:9200/word-index"
curl -XDELETE "http://elastic:9200/tweet-index"

curl -XPUT "http://elastic:9200/word-index/" -H 'Content-Type: application/json' --data "@word-index.json"
curl -XPUT "http://elastic:9200/tweet-index/" -H 'Content-Type: application/json' --data "@tweet-index.json"


curl -X PUT "http://elastic:9200/_rollup/job/word-rollup-job" -H 'Content-Type: application/json' --data "@word-rollup-job.json"

curl -X POST "localhost:5601/kibana/api/saved_objects/_import?createNewCopies=true" -H "kbn-xsrf: true" --form file="@export_kibana.ndjson" -H 'kbn-xsrf: true'./