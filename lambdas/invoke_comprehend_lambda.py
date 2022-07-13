# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import boto3
import os
import logging




logger = logging.getLogger()
logger.setLevel(logging.INFO)

comprehend = boto3.client("comprehend")

def lambda_handler(event, context):
    
    endpointArn = os.environ.get("ENDPOINT_ARN")
    response = comprehend.describe_endpoint(EndpointArn=endpointArn)
    status = response['EndpointProperties']['Status']
    if status in ['CREATING', 'UPDATING', 'DELETING' ,'FAILED']:
        responseBody = 'Amazon Comprehend endpoint not created or Model training in progress'
        return {
                'statusCode': 200,
                'body': json.dumps(responseBody)
            }
    else:
        try:
        # calling Custom Comprehend Named entity recognition API in real time
        # to fetch product and its version details from the email message body
            response_Entity = comprehend.classify_document (
            EndpointArn=endpointArn, Text=event['Text']
        )
            responseBody = response_Entity['Classes']
            
        except Exception as e:
         # Send some context about this error to Lambda Logs
            logger.error("Exception (%s)", e)
            raise e
            
            
    return {
          'statusCode': 200,
          'body': responseBody
          
          }