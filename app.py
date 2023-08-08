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

sns = boto3.client('sns', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name="us-east-2")


def create_subscriptions(topicArn, protocol, endpoint):
    response = sns.subscribe(TopicArn=topicArn, Protocol=protocol, Endpoint=endpoint, ReturnSubscriptionArn=True)
    return response['SubscriptionArn']


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
    emails = [request.form.get(f"email{i}") for i in range(1, 6) if request.form.get(f"email{i}")]
    user_email = request.form.getlist("your_email")
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)

    # Upload file to AWS S3
    s3_client = boto3.client("s3", aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
    s3_key = "media/" + filename
    s3_client.upload_fileobj(uploaded_file, AWS_STORAGE_BUCKET_NAME, s3_key)

    conn = psycopg2.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME, port='5432')
    cur = conn.cursor()
    for email in emails:
        cur.execute(
            "INSERT INTO fileuploadtable(user_email, email, filename) VALUES(%s, %s, %s);",
            (user_email, email, s3_key))

    conn.commit()
    # Trigger Lambda function
    file_url = s3_client.generate_presigned_url('get_object', Params={'Bucket': AWS_STORAGE_BUCKET_NAME, 'Key': s3_key},
                                                ExpiresIn=3600)

    message = "Hello, Click on the link to download the file from s3:   \n{}".format(file_url)
    topic = sns.create_topic(Name="akaasula_topic")
    for email in emails:
        if email:
            topicArn = topic['TopicArn']
            protocol = 'email'
            endpoint = email
            response = create_subscriptions(topicArn, protocol, endpoint)
            sns.publish(TopicArn=topicArn, Subject="click the link to download the file  ",
                        Message=message)

    # lambda_client = boto3.client("lambda", aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY,
    #                              region_name="us-east-2")
    # lambda_payload = {
    #     "file_link": file_url,  # Replace with actual file link
    #     "email_addresses": emails
    # }
    # lambda_response = lambda_client.invoke(
    #     FunctionName="akaasula_function",
    #     InvocationType="Event",
    #     Payload=json.dumps(lambda_payload)
    # )
    print("ALL DONE")

    return redirect("/")  # Redirect to desired page after processing


@app.route('/add', methods=["POST"])
def add():
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")

    if password != confirm_password:
        print("passwords do not match")
    # f = request.files['file']
    # filename = secure_filename(f.filename)
    #
    # # AWS S3 client setup
    # s3_client = boto3.client("s3", aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
    #
    # # Upload file to S3 bucket
    # s3_key = "media/" + filename
    # s3_client.upload_fileobj(f, AWS_STORAGE_BUCKET_NAME, s3_key)

    # Database insertion
    try:

        conn = psycopg2.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME, port='5432')
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO userdetails(name, email, password) VALUES(%s, %s, %s);",
            (name, email, password)
        )
        conn.commit()
        return render_template('upload.html')
    except Exception as e:
        print("Connection failed due to {}".format(e))
        return redirect("/")

    # f.close()


@app.route('/')
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
            "CREATE TABLE userdetails( name VARCHAR(100), email VARCHAR(100), password VARCHAR(50));")
        print("table created")
        cur.execute(
            "CREATE TABLE fileuploadtable(user_email VARCHAR(150), email VARCHAR(150), filename VARCHAR(200) );")
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
