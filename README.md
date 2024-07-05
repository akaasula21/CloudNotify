
# CloudNotify

This is a Flask web application that provides a simple file sharing platform. Users can register, log in, and upload files to an Amazon Web Services (AWS) S3 bucket. The application also integrates with AWS Simple Notification Service (SNS) to send email notifications to specified recipients when files are uploaded. Additionally, it utilizes PostgreSQL for user and file data storage.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Endpoints](#endpoints)
- [Database](#database)
- [AWS Integration](#aws-integration)
- [License](#license)

## Prerequisites

Before running the application, make sure you have the following prerequisites installed:

- Python 3.x
- Flask
- psycopg2 (PostgreSQL adapter for Python)
- boto3 (AWS SDK for Python)
- PostgreSQL
- AWS S3 Bucket
- AWS SNS Topic
- AWS RDS PostgreSQL Database


## Installation

1. Clone this repository to your local machine:

```bash
    git clone https://github.com/yourusername/your-repo.git

```
2. Navigate to the project directory:

```bash
    cd your-repo
```
3. Create a virtual environment and activate it (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate
```
4. Install the required Python packages:
```bash
pip install Flask psycopg2 boto3
```



## Configuration

Before running the application, you need to configure your AWS credentials and database connection details. Open the app.py file and locate the following variables at the top:

- ACCESS_KEY: Your AWS access key.
- SECRET_KEY: Your AWS secret key.
- AWS_STORAGE_BUCKET_NAME: The name of your AWS S3 bucket.
- ENDPOINT: The endpoint for your AWS RDS PostgreSQL database.
- PORT: The database port (default is 5432).
- USR: Your database username.
- PASSWORD: Your database password.
- DBNAME: The name of your PostgreSQL database.

Replace these values with your own credentials and settings.
## Usage

To run the application, execute the following command in your terminal:

```bash
python app.py
```
The application will start and be accessible at http://localhost:5000 in your web browser.

## Endpoints

- /: The main login page.
- /notfound: Page displayed when a user is not found.
- /login: Login page.
- /register: User registration page.
- /upload: Endpoint for uploading files to AWS S3.
- /add: Endpoint for adding new users.
- /mainpage: Main application page after successful login.
- /initialize: Initializes the database tables.
## Database
This application uses PostgreSQL as its database. The database schema includes two tables:

1. userdetails: Stores user information, including name, email, and password.

2. fileuploadtable: Stores file upload information, including the user's email, recipient emails, and the filename in AWS S3.

You can initialize the database by visiting the /initialize endpoint, which creates these tables if they do not already exist.

## AWS Integration

- The application utilizes AWS S3 for storing uploaded files. Files are uploaded to the specified S3 bucket.

- AWS SNS is used to send email notifications to specified recipients when files are uploaded. Notifications are sent for each recipient specified during the file upload process.

- To enable these integrations, you must configure your AWS credentials and provide the appropriate bucket name and SNS topic name in the code.
