from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import boto3
import json
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import os

ACCESS_KEY = "AKIA6AN2GCBWFE2ZXYNR"
SECRET_KEY = "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"
AWS_STORAGE_BUCKET_NAME = 'akaasulabucket'

ENDPOINT = "database-6.ctpgewovurvk.us-east-2.rds.amazonaws.com"
PORT = "5432"
USR = "akaasula"
PASSWORD = "adarsh123"
DBNAME = "postgres"

app = Flask(__name__)


@app.route('/')
def main():
    return render_template("login.html")


@app.route('/notfound')
def notfound():
    return render_template("usernotfound.html")


@app.route('/login')
def login():
    render_template("login")


@app.route('/register')
def register():
    return render_template("register.html")


@app.route('/upload', methods=["POST"])
def upload():
    # Get user information from the session or any authentication mechanism you're using
    user_email = session.get("user_email")  # Replace with your actual user authentication logic

    if user_email:
        f = request.files['file']
        filename = secure_filename(f.filename)

        # AWS S3 client setup
        s3_client = boto3.client("s3", aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

        # Upload file to S3 bucket
        s3_key = "media/" + filename
        s3_client.upload_fileobj(f, AWS_STORAGE_BUCKET_NAME, s3_key)

        # Database insertion
        conn = psycopg2.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME, port='5432')
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO userdetails(email, imagelocation) VALUES(%s, %s);",
            (user_email, s3_key)
        )
        conn.commit()
        f.close()

        # Lambda and SES integration (if needed)

        return redirect("/mainpage")  # Redirect to the main page or wherever you want
    else:
        return redirect("/login")  # Redirect to the login page if not logged in


@app.route('/add', methods=["POST"])
def add():
    email = request.form.get("email")
    password = request.form.get("password")
    desc = request.form.get("description")
    f = request.files['file']
    filename = secure_filename(f.filename)

    # AWS S3 client setup
    s3_client = boto3.client("s3", aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

    # Upload file to S3 bucket
    s3_key = "media/" + filename
    s3_client.upload_fileobj(f, AWS_STORAGE_BUCKET_NAME, s3_key)

    # Database insertion
    conn = psycopg2.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME, port='5432')
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO userdetails(email, password, description, imagelocation) VALUES(%s, %s, %s, %s);",
        (email, password, desc, s3_key)
    )
    conn.commit()
    f.close()

    # Lambda and SES integration
    lambda_client = boto3.client('lambda', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name='us-east-2')
    lambda_payload = {"email": email}
    lambda_client.invoke(FunctionName='lambdaSNS', InvocationType='Event', Payload=json.dumps(lambda_payload))

    return redirect("/")




@app.route('/mainpage', methods=["GET"])
def mainpage():
    email = request.args.get('email')
    password = request.args.get('password')
    print(email, password)
    try:
        conn = psycopg2.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME, port='5432')
        cur = conn.cursor()
        qry = "SELECT * FROM userdetails Where email ='" + email + "' AND password = '" + password + "';"
        print(qry)
        cur.execute("SELECT * FROM userdetails;")
        query_results = cur.fetchall()
        print(query_results)
        cur.execute("SELECT * FROM userdetails Where email ='" + email + "' AND password = '" + password + "';")
        query_results = cur.fetchall()
        print(query_results)
        if len(query_results) == 1:
            return render_template("mainpage.html")
        else:
            return redirect("/notfound")
    except Exception as e:
        print("Database connection failed due to {}".format(e))
        return redirect("/")


@app.route('/search', methods=["POST"])
def search():
    email = request.form.get("email")
    print(email)
    return redirect("viewdetails/" + str(email))


@app.route('/viewdetails/<email>')
def viewdetails(email):
    try:
        conn = psycopg2.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME, port='5432')
        cur = conn.cursor()
        cur.execute("SELECT * FROM userdetails Where email ='" + email + "';")
        conn.commit()
        query_results = cur.fetchall()
        print(query_results)
        client = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
        url = client.generate_presigned_url('get_object',
                                            Params={
                                                'Bucket': 'applab1',
                                                'Key': 'images/' + str(query_results[0][3]),
                                            },
                                            ExpiresIn=3600)
        url = str(url).split('?')[0]
        item = {'email': query_results[0][0], 'password': query_results[0][1], 'desc': query_results[0][2], 'link': url}
        print(item)
        return render_template("viewdetails.html", item=item)
    except Exception as e:
        print("Database connection failed due to {}".format(e))
        return redirect("/")


@app.route('/initialize')
def initialize():
    try:
        print("INITIALIZING DATABASE")
        conn = psycopg2.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME, port='5432')
        cur = conn.cursor()
        try:
            cur.execute("DROP TABLE IF EXISTS userdetails;")
            print("table deleted")
        except Exception as e:
            print("cannot delete table")
        cur.execute(
            "CREATE TABLE userdetails(email VARCHAR(20), password VARCHAR(20), description VARCHAR(50), imagelocation VARCHAR(50));")
        print("table created")

        conn.commit()

        cur.execute("SELECT * FROM userdetails;")
        query_results = cur.fetchall()
        print(query_results)
        return redirect("/")
    except Exception as e:
        print("Database connection failed due to {}".format(e))
        return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
