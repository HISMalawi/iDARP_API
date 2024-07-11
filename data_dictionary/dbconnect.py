import os
import mysql.connector as mysql
import psycopg2


# E-mastercard database
def connectEmcDB():
    try:
        db = psycopg2.connect(
            host=os.environ['EMC_HOST'],
            database=os.environ['EMC_DATABASE'],
            user=os.environ['EMC_USER'],
            password=os.environ['EMC_PASSWORD']
        )
        return db

    except Exception as e:
        # logg the error
        print(str(e))
        return None


# Point of Care database
def connectPocDB():
    try:
        db = psycopg2.connect(
            host=os.environ['POC_HOST'],
            database=os.environ['POC_DATABASE'],
            user=os.environ['POC_USER'],
            password=os.environ['POC_PASSWORD']
        )
        return db

    except Exception as e:
        # logg the error
        print(str(e))
        return None


def connectGcpDB():
    try:
        db = mysql.connect(
            host=os.environ['GCP_HOST'],
            database=os.environ['GCP_DATABASE'],
            user=os.environ['GCP_USER'],
            password=os.environ['GCP_PASSWORD']
        )
        return db

    except Exception as e:
        # logg the error
        print(str(e))
        return None