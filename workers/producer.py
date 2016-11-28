import os

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from textwrap import TextWrapper

from kafka import KafkaProducer
import json
import time,math

producer = KafkaProducer(value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                         bootstrap_servers='localhost:9092')

access_token = ""
access_token_secret = ""
consumer_key = ""
consumer_secret = ""


class StdOutListener(StreamListener):
    status_wrapper = TextWrapper(width=60, initial_indent='    ', subsequent_indent='    ')

    def on_data(self, data):
        try:
            json_data = json.loads(data)
            if json_data['geo'] is not None:
                data = {
                    'geo': json_data['geo'],
                    'id': json_data['id'],
                    'text': json_data['text'].encode('utf-8'),
                    'user': json_data['user'],
                    'fetched': math.floor(time.time())
                }
                producer.send('test', data)
                print "Found"
            else:
                print "No Geo"

        except StandardError as e:
            raise e

l = StdOutListener()
auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
stream = Stream(auth, l)

stream.filter(track=['nyc', 'brooklyn', 'nyu'])
