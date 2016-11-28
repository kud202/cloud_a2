from kafka import KafkaConsumer
from alchemyapi_python.alchemyapi import AlchemyAPI
import json
import boto3

consumer = KafkaConsumer('test',
                         value_deserializer=json.loads,
                         bootstrap_servers='localhost:9092')

alchemyapi = AlchemyAPI()

sns = boto3.client('sns')

for msg in consumer:
    response = alchemyapi.sentiment('text',msg.value['text'])
    if response['status'] == 'OK':
        tweetInfo = msg.value
        tweetInfo['sentiment'] = response['docSentiment']
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:104807864716:senti_tweets',
            Message=json.dumps(tweetInfo),
            Subject='SentiTweet'
        )
        print (tweetInfo)
