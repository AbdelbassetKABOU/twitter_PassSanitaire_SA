# On importe les Operators dont nous avons besoin.
from pymongo import MongoClient 
from csv import reader
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from datetime import datetime, timedelta 
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import json
import time
import pandas as pd
from pymongo import MongoClient
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sqlalchemy import text, create_engine, Date, func
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from bson import json_util
import config
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from dateutil import parser




default_args = {
    'owner': 'airflow',
    'email': ['airflow@airflow.com'],
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}
dag = DAG(
    'pass_dag',
    default_args=default_args,
    description='Airflow 101',
    #start_date=datetime(2021,01,01)
    start_date=days_ago(2),
    schedule_interval=timedelta(days=1),
)


t0 = BashOperator(
    task_id='salutation',
    bash_command='echo "bonjouuuuuuuuuuuuuurrrrrr"; exit 99;',
    dag=dag,
)


# connect to local MongoDB
client = MongoClient(config.MONGODB_HOST, config.MONGODB_PORT)
db = client.tweets
tweets = db.tweets


def parse_json(data):
    return json.loads(json_util.dumps(data))


def extract():
    """Extracts all tweets from the MongoDB database as a list"""
    # define a timestamp to only extract newest data
    last_extraction_date = datetime.utcnow() - timedelta(minutes=1)
    print ("=======================>>>>>>>>>>>")
    print (type(tweets.find({"timestamp": {"$gte": last_extraction_date}})))
    parsed_json = parse_json (tweets.find({"timestamp": {"$gte": last_extraction_date}}))
    #extracted_tweets = list(tweets.find({"timestamp": {"$gte": last_extraction_date}}))
    extracted_tweets = list(parsed_json)

    #extracted_tweets
    return extracted_tweets


# define tasks
#t1 = PythonOperator(task_id="extract", x_com_push=True, python_callable=extract, dag=dag)
t1 = PythonOperator(task_id="extract", python_callable=extract, dag=dag)


def transform(**context):
    """
    Performs sentiment analysis on the tweets and returns it in a format so
    the tweets can be written into a Postgres database
    """
    analyzer = SentimentIntensityAnalyzer()
    extract_connection = context["ti"]
    extracted_tweets = extract_connection.xcom_pull(task_ids="extract")
    transformed_tweets = []
    for tweet in extracted_tweets:
        vs = analyzer.polarity_scores(tweet["text"])
        tweet["pos"] = vs["pos"]
        tweet["neu"] = vs["neu"]
        tweet["neg"] = vs["neg"]
        tweet["compound"] = vs["compound"]
        transformed_tweets.append(tweet)
    #print (transformed_tweets)
    return transformed_tweets


t2 = PythonOperator(task_id="transform", provide_context=True, python_callable=transform, dag=dag)







# set parameters for local postgresDB
DATABASE_USER = config.DATABASE_USER
DATABASE_PASSWORD = config.DATABASE_PASSWORD
DATABASE_HOST = config.DATABASE_HOST
DATABASE_PORT = config.DATABASE_PORT
DATABASE_DB_NAME = config.DATABASE_DB_NAME

# connect to postgres
conns = f"postgres://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_DB_NAME}"
postgres_db = create_engine = create_engine(conns, encoding="utf-8")

# create table for twitter data from mongodb
create_query = """
CREATE TABLE IF NOT EXISTS tweets_sentiments (
tweet_id SERIAL PRIMARY KEY,
tweet_username VARCHAR(255),
tweet_text TEXT,
tweet_followers_count INTEGER,
tweet_timestamp TIMESTAMP,
tweet_location VARCHAR(255),
tweet_keyword VARCHAR(50),
tweet_neg REAL,
tweet_neu REAL,
tweet_pos REAL,
tweet_compound REAL
);
"""

'''
create_query = """
CREATE TABLE IF NOT EXISTS tweets_sentiments (
tweet_id SERIAL PRIMARY KEY,
tweet_username VARCHAR(255),
tweet_text TEXT,
tweet_followers_count INTEGER,
tweet_timestamp TIMESTAMP
tweet_location VARCHAR(255),
tweet_keyword VARCHAR(50),
tweet_neg REAL,
tweet_neu REAL,
tweet_pos REAL,
tweet_compound REAL
);
"""
'''

# run query
postgres_db.execute(create_query)



def load(**context):
    """Load transformed data into the Postgres database"""
    # extract data from context
    extract_connection = context["ti"]
    transformed_tweets = extract_connection.xcom_pull(task_ids="transform")
    #transformed_tweets = transformed_tweets)
    insert_query = """
    INSERT INTO tweets_sentiments VALUES (
    DEFAULT, 
    :username, 
    :text, 
    :followers, 
    :timestamp, 
    :location, 
    :keyword, 
    :neg, 
    :neu, 
    :pos, 
    :compound
    );"""



    # load data into postgres one by one
    for tweet in transformed_tweets:
        #print ("---------------------------------->>>>>>",json.dumps(tweet["timestamp"]))
        mydate = json.dumps(tweet["timestamp"])
        timestamp = mydate[10:-1] 
        timestamp = datetime.utcfromtimestamp(int(timestamp)//1000)
        #timestamp = datetime(parser.parse(timestamp))
        #timestamp = func.to_timestamp(timestamp).cast(Date)
        print ("---------------------------------->>>>>>", timestamp)
        #tweet = parse_json (atweet)
        postgres_db.execute(
            text(insert_query),
            {
                "username": tweet["username"],
                "text": tweet["text"],
                "followers": tweet["followers_count"],
                #"timestamp": json.dumps(tweet["timestamp"]),
                "timestamp": timestamp,
                "location": tweet["location"],
                "keyword": tweet["keyword"],
                "neg": tweet["neg"],
                "neu": tweet["neu"],
                "pos": tweet["pos"],
                "compound": tweet["compound"]
            },
        )

t3 = PythonOperator(task_id="load", provide_context=True, python_callable=load, dag=dag)




t0 >> t1 >> t2 >> t3


# [1] https://stackoverflow.com/questions/56808425/sqlalchemy-psycopg2-programmingerror-cant-adapt-type-dict
