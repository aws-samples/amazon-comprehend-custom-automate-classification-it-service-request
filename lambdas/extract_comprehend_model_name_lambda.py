# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import boto3
import time
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

comprehend = boto3.client("comprehend")
sns = boto3.resource("sns")

def lambda_handler(event, context):
    bucketname =  event['Records'][0]['s3']['bucket']['name']
    classifierobject =  event['Records'][0]['s3']['object']['key']
    searchkey='s3://'+ bucketname + '/' + classifierobject
    topic_arn = os.environ.get("TOPIC_ARN")
    sns.Topic(arn=topic_arn).publish(Message='Completed Amazon Comprehend custom classifier training')
    try:
        # Extract Amazon Comprehend document classfier arn
        documentclassifierarn=''
        document_classifier_list = comprehend.list_document_classifiers()
        
        for i in document_classifier_list:
            if(i in 'DocumentClassifierPropertiesList'):
                documentclassifierlist=list(filter(lambda k:k['OutputDataConfig']['S3Uri']==searchkey, document_classifier_list[i]))
                if not documentclassifierlist:
                    documentclassifierarn='Document Classifier ARN not found'
                    logger.info('Document Classifier ARN not found')
                    sns.Topic(arn=topic_arn).publish(Message=documentclassifierarn)
                else:
                    documentclassifierarn=documentclassifierlist[0]['DocumentClassifierArn']
                    logger.info('Document Classifier ARN: ' + documentclassifierarn)
                    message = 'Amazon Comprehend Classifier Model ARN : ' + documentclassifierarn
                    sns.Topic(arn=topic_arn).publish(Message=message)
                    
    except Exception as e: 
            logger.error("Exception (%s)", e)
            raise e

    return {
        'statusCode': 200,
        'EndpointArn': documentclassifierarn
    }
