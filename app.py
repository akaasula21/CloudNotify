from flask import Flask, render_template, request, redirect, url_for
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


@app.route('/add', methods=["POST"])
def add():
    email = request.form.get("email")
    password = request.form.get("password")
    desc = request.form.get("description")
    #  imagepath=request.form.get("imagefilepath")
    f = request.files['file']
    filename = f.filename.split("\\")[-1]
    f.save(secure_filename(filename))
    # filename=imagepath.split("\\")[-1]

    client = boto3.client("s3",
                          aws_access_key_id="AKIA6AN2GCBWFE2ZXYNR",
                          aws_secret_access_key="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",
                          # aws_session_token="FwoGZXIvYXdzELX//////////wEaDPWvF69TancW7W8QECK8AfVQ2bketm8GGXxu/jQj8xN5igYCtViBqbo1vgEnZgnsW3xX6WJkShy30InHduHjECJcx3OC/9+PBSOSUKIT9xJvL3v5LdH6IwNtEOf0+tt+naZk40zDF/ZoersHU4UOCer+eYcVS27haByKQY0JJtiiGlxXcazVcyykoqNTORxtHgExkRlJ58vwcuLXBTmBOdFWyKN8QFke+tmnebdfs0rOVZwc9fCvsNseS0k6h2tEhHBSUJH19pXnJkd1KJuTyqUGMi175Qaybc9XNONF479KVknYfWkWr7gH3yY37A00jTOb+UCeJ5jbI2LWNS5FkGg="

                          )
    client.upload_file(filename, AWS_STORAGE_BUCKET_NAME, "media/" + filename)

    conn = psycopg2.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME, port='5432')
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO userdetails(email,password,description,imagelocation) VALUES('" + email + "','" + password + "','" + desc + "', '" + filename + "');")
    print("Insert Success")
    conn.commit()
    os.remove(filename)

    lambda_client = boto3.client('lambda',
                                 aws_access_key_id=ACCESS_KEY,
                                 aws_secret_access_key=SECRET_KEY,
                                 region_name='us-east-2')

    lambda_payload = {"email": email}
    lambda_client.invoke(FunctionName='lambdaSNS',
                         InvocationType='Event',
                         Payload=json.dumps(lambda_payload))

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
            cur.execute("DROP TABLE userdetails;")
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
