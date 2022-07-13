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


def on_event(event, context):
    
    request_type = event['RequestType'].lower()
    if request_type == 'create':
        return on_create(event)
    if request_type == 'update':
        return on_update(event)
    if request_type == 'delete':
        return on_delete(event)
    raise Exception(f'Invalid request type: {request_type}')
  

def on_create(event):
    props = event["ResourceProperties"]
    logger.info("create new resource with props %s" % props)
    
    documentclassifierarn=props['documentclassifierarn']
    logger.info('Document Clasifier ARN : ' + documentclassifierarn )
    # add your create code here...
    response = comprehend.create_endpoint(EndpointName="comprehend-endpoint"+str(int(round(time.time() * 1000))), ModelArn = documentclassifierarn,
          DesiredInferenceUnits=1)
    
    physical_id = response['EndpointArn']
  
    return { 'PhysicalResourceId': physical_id ,
            'Data': response
        
    }
    
  
def on_update(event):
    endpointarn = event["PhysicalResourceId"]
    props = event["ResourceProperties"]
    documentclassifierarn=props['documentclassifierarn']
    logger.info("update resource %s with props %s" % (endpointarn, documentclassifierarn))
    comprehend.update_endpoint(EndpointArn=endpointarn,DesiredModelArn=documentclassifierarn,DesiredInferenceUnits=1 )
    
    
  
def on_delete(event):
    endpointarn = event["PhysicalResourceId"]
    logger.info("delete resource %s" % endpointarn)
    comprehend.delete_endpoint(EndpointArn=endpointarn)
    