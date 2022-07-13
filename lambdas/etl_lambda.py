# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import csv
import sqlite3
import zipfile
import bz2
import glob
import botocore
import boto3
import json
import urllib.parse
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.resource("s3")
sns = boto3.resource("sns")


def _upload_file(bucket, class_name, local_file):
    # Upload the file to S3 from EFS
    try:
        key = "prepped_data/" + class_name.lower() + ".csv"
        s3.Bucket(bucket).upload_file(local_file, key)
    except botocore.exceptions.ClientError as e:
        logger.error("Exception (%s)", e)
        logger.error(
            "Error uploading object %s from bucket %s to EFS. Make sure they exist and your bucket is in the same region as this function.", key, bucket)
        raise e

    logger.info("Uploaded file: %s of size %d bytes to %s", local_file,
                os.path.getsize(local_file), "s3://" + bucket + "/" + key)


def _download_file(bucket, key, local_dir, local_zip_file):
    # Download the zip file to EFS file system
    try:
        s3.Bucket(bucket).download_file(key, local_dir + "/" + local_zip_file)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            logger.error("The object does not exist.")
        else:
            logger.error("Exception (%s)", e)
            logger.error(
                "Error downloading object %s from bucket %s to EFS. Make sure they exist and your bucket is in the same region as this function.", key, bucket)
            raise e
    logger.info("Downloaded zip file: %s ", local_dir + "/" + local_zip_file)


def _unzip_file(local_dir, local_zip_file):

    # unzip the file
    try:
        with zipfile.ZipFile(local_dir + "/" + local_zip_file, 'r') as zip_ref:
            zip_ref.extractall(local_dir)

        # the zip file contains multiple .bz2 files, for each .bz2 file
        for filepath in glob.glob(local_dir + "/*.bz2"):
            zfile = bz2.BZ2File(filepath)  # open the file
            data = zfile.read()  # get the decompressed data
            newfilepath = filepath[:-4]  # the filepath ends with .bz2
            with open(newfilepath, 'wb') as f:
                f.write(data)  # write a uncompressed file

    except Exception as e:
        logger.error("Exception (%s)", e)
        logger.error("Error extracting zip file %s",
                     local_dir + "/" + local_zip_file)
        raise e

    logger.info("Unzipped file: %s", local_dir + "/" + local_zip_file)


def _extract_bug_summary(db_path,
                         class_name,
                         local_file_name,
                         bucket):

    # execute SQLLite Query on the downloaded data set
    try:
        with sqlite3.connect(db_path) as conn:
            with open(local_file_name, "w") as f:
                csvWriter = csv.writer(f)
                c = conn.cursor()
                c.execute("SELECT (?) AS type, summary || ' ' || description FROM issue WHERE type = 'Bug' AND summary IS NOT NULL AND description IS NOT NULL",
                          (class_name,))
                rows = c.fetchall()
                count = len(rows)
                logger.info("Fetched %d rows for %s", count, class_name)
                csvWriter.writerows(rows)

        _upload_file(bucket, class_name, local_file_name)

    except Exception as e:
        logger.error("Exception (%s)", e)
        logger.error(
            "Error extracting data from sqlite3 data file %s", db_path)
        raise e

    logger.info("Training data has been created in S3 bucket for %s", class_name)


def _extract_csv(bucket,
                 local_dir):

    # for all sqlite3 files
    for db_path in glob.glob(local_dir + "/*.sqlite3"):

        # db_path  will be /mnt/data/hadoop.sqlite3
        # file_name will be hadoop.sqlite3
        # class_name will be HADOOP
        # output_file_name will be /mnt/data/hadoop.csv

        file_name = db_path.split("/")[-1]
        class_name = file_name.split(".")[0].upper()
        output_file_name = local_dir + "/" + file_name + ".csv"

        logger.info("Extracting training data for %s", class_name)
        _extract_bug_summary(db_path,
                             class_name,
                             output_file_name,
                             bucket)


def _notify_etl_completed(topic_arn):

    sns.Topic(arn=topic_arn).publish(
        Message='ETL completed and prepped data uploaded to S3',
        MessageAttributes = {
        'event_type': {
            'DataType': 'String',
            'StringValue': 'ETL completed and prepped data uploaded to S3'
            }
        
        }
    )
    logger.info("Notification complete")


def lambda_handler(event, context):

    logger.info("Received event: " + json.dumps(event))

    # find the bucket and key from the event object
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(
        event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    topic_arn = os.environ.get("TOPIC_ARN")

    local_dir = "/mnt/data"
    local_zip_file = "raw_data.zip"

    _download_file(bucket, key, local_dir, local_zip_file)
    _unzip_file(local_dir, local_zip_file)
    _extract_csv(bucket, local_dir)
    _notify_etl_completed(topic_arn)

    logger.info("Completed the event trigger.")

    return {
        "event": event,
        "status": "SUCCEEDED",
    }
