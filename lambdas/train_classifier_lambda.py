# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import uuid
import csv
import botocore
import boto3
import json
import urllib.parse
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.resource("s3")
comprehend = boto3.client("comprehend")
sns = boto3.resource("sns")


def _start_comprehend_job(bucket_name, comprehend_role_arn):

    logger.info("Starting Amazon Comprehend job")

    uuid_str = str(uuid.uuid4())

    response = comprehend.create_document_classifier(
        DocumentClassifierName="ComprehendCustomClassifier" + "-" + uuid_str,
        VersionName="v1",
        DataAccessRoleArn=comprehend_role_arn,
        InputDataConfig={
            "DataFormat": "COMPREHEND_CSV",
            "S3Uri": "s3://" + bucket_name + "/prepped_data/"},
        OutputDataConfig={
            "S3Uri": "s3://" + bucket_name + "/output_data/",
        },
        ClientRequestToken=uuid_str,
        LanguageCode="en",
        Mode="MULTI_CLASS")

    logger.info("Amazon Comprehend Job submitted, Response :%s", response)
    classifier_arn = response['DocumentClassifierArn']
    return (classifier_arn)
    
    


def lambda_handler(event, context):

    logger.info("Received event notification from SNS Topic: " +
                json.dumps(event))

    # find the bucket
    bucket_name = os.environ.get("BUCKET_NAME")
    comprehend_role_arn = os.environ.get("COMPREHEND_DATA_ACCESS_ROLE_ARN")
    topic_arn = os.environ.get("TOPIC_ARN")

    job = _start_comprehend_job(bucket_name, comprehend_role_arn)
    logger.info("Started Amazon Comprehend classifier training %s", job)
    sns.Topic(arn=topic_arn).publish(
        Message='Started Amazon Comprehend classifier training'
        
    )

    return {
        "event": event,
        "status": "SUCCEEDED",
    }
