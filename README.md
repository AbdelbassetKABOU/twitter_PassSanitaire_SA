## Twitter_PassSanitaire_SA

This is a Docker pipeline with ETL job (extract, transform, load) managed through Airflow.

We are concerned by the sentiment analysis of tweets with hashtag related to the _pass_sanitaire_, a European Union digital *Covid* certificate introduced in France in June 2021, during the *Covid-19* pandemic [1].  

The project was behind a huge company on twitter against the law. In this repo, we are concerned by the Sentiment Analysis of tweets related to this context. In particular, we are concerned by the followings hashtags :

- *#passsanitaire,*
- *#passeportsanitaire,*
- *#stoppasssanitaire,*
- *#nonaupasssanitaire,*
- *#PassSanitaireDeLaHonte,*
- *#StopDictatureSanitaire,*
- *#BoycottPassSanitaire,*
- *#DictatureSanitaire,*
- *#AntiPassSanitaire,*
- *#PassDeLaHonte,*
- *#NonAuPassDeLaHonte*

### Components

The pipeline is composed of six (6) docker containers, as follows : 

- __pass_tweet_collector__ : Responsible of collecting the tweets with the previous hashtags,
- __pass_webserver_1__ : A separate container for the airflow webserver, based on *apache/airflow* official image [2] *(and not the puckel/docker-airflow one [3])*,
- __pass_scheduler_1__ : A separate docker container for the Airflow scheduler *(based on apache/airflow)*,
- __pass_postgres_1__ : A docker container for the Postgres database. This is used both as a backend engine for Airflow for more performance compared to SQLite, the by default database engine.
- __pass_mongodb_1__ : The docker container of the MongoDB database. This is used in the *extract* task as a database to store the downloaded tweets.
- __pass_meta_1__ : A container for *Metabase* BI tool [4] based on *metabase/metabase* docker-hub image [5],

![Alt text](images/dockerps.png?raw=true "Title")

### Workflow

- Extract : 
    - Collect tweets through *Twitter API* [6] (keys introduced in ./tweet_collector/config.py)
    - Store Tweets in the *MongoDB* database
- Transform :
    - reload the tweets from the *MongDB*, 
    - Perform some sentiment analysis routines using the simple *vaderSentiment* package [7],
    - Add calculated insight to each tweet,
    - Store again in *MongoDB*, both the tweets and the resulting calculations (in a new columns),
- Load :
    - Store transformed tweets in *Postgres* database,
    - A user can easily access the database through *Metabase* *(c.f. figures bellow)*, add visualizations, dashboard, etc.


### Notes

The code is partially based on Airflow course from *Datascientest.com* [8] and the pipeline proposed in [9]. 

### Snapshots


![Alt text](images/dag.png?raw=true "Title")

![Alt text](images/dag_2.png?raw=true "Title")

![Alt text](images/metabase_01.png?raw=true "Title")

![Alt text](images/metabase_02.png?raw=true "Title")

![Alt text](images/metabase_03.png?raw=true "Title")


## References

[2] https://hub.docker.com/r/apache/airflow

[3] https://hub.docker.com/r/puckel/docker-airflow

[4] https://www.metabase.com/docs/latest/users-guide/01-what-is-metabase.html

[5] https://hub.docker.com/r/metabase/metabase

[6] https://developer.twitter.com/en/docs/twitter-api

[7] https://pypi.org/project/vaderSentiment/

[8] https://datascientest.com/apache-airflow

[9] https://github.com/senzelden/twitter_data_pipeline

