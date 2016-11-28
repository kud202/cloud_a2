import json
import os
import re
import sys
import urllib2

import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
from flask import Flask, render_template, g
from flask import request, abort, send_from_directory
from requests_aws4auth import AWS4Auth

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

reload(sys)
sys.setdefaultencoding('utf8')

application = Flask(__name__)


def get_es():
    es = getattr(g, '_es', None)
    if not es:
        session = boto3.Session()
        credentials = session.get_credentials()
        region = os.environ['AWS_REGION'] if 'AWS_REGION' in os.environ else 'us-east-1'

        host = 'search-kudtweet-ft7eeowl5of55zhqx2lq3fnxwm.us-east-1.es.amazonaws.com'
        awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'es',
                           session_token=credentials.token)

        es = Elasticsearch(
            hosts=[{'host': host, 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )
        g._es = es
    return es


@application.route('/')
def search():
    term = request.args.get('term', "nyc")
    return render_template('index.html', prev_term=term)


@application.route('/new')
def new():
    term = request.args.get('term')
    frm = int(request.args.get('from'))
    query = {
        "query": {
            "bool": {
                "should": {
                    "match": {
                        "text": term
                    }
                },
                "filter": {
                    "range": {
                        "fetched": {
                            "gte": frm
                        }
                    }
                }
            }
        }
    }
    print(query)
    res = get_es().search(index="idx_twp5", body=query)
    return json.dumps(res['hits']['hits'])


def save():
    j = request.get_json(force=True)
    get_es().index(index="idx_twp5",
                   doc_type="tweet",
                   body=json.loads(j['Message']))
    return "OK"


@application.route('/static/<path:path>')
def send_js(path):
    return send_from_directory('static', path)


@application.route('/sns', methods=['POST'])
def sns():
    msg_type = request.headers.get('x-amz-sns-message-type')
    if msg_type == 'SubscriptionConfirmation':
        return subscribe()
    elif msg_type == 'Notification':
        return save()

    else:
        abort(400)


def subscribe():
    j = request.get_json(force=True)
    urllib2.urlopen(j['SubscribeURL'])
    return "OK"


if __name__ == '__main__':
    application.run(host='0.0.0.0')
