import mysql.connector as mysql

def connectDB():
    db = mysql.connect(
        host="34.71.119.33",
        user="admin",
        passwd="Very*secure",
        database="dev_test"
    )
    return db
