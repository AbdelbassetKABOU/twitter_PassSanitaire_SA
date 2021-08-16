#!/usr/bin/env bash
#pip install -r ./scripts/requirements.txt
pip install -r /opt/airflow/scripts/requirements.txt
pip install pymongo
airflow db init
airflow users create -r Admin -u admin -e admin@example.com -f admin -l user -p admin
airflow webserver -w 1
