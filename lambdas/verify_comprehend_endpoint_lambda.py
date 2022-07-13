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

def is_complete(event, context):

    endpointarn = event["PhysicalResourceId"]
    is_ready=False

  # check if resource is stable based on request_type
    try:
        endpointstatus=comprehend.describe_endpoint(EndpointArn=endpointarn)
        logger.info(endpointstatus['EndpointProperties']['Status'])
        if(endpointstatus['EndpointProperties']['Status']=='IN_SERVICE'):
           
            logger.info('EndPoint is in Created State')
            is_ready = True
            
        elif(endpointstatus['EndpointProperties']['Status']=='CREATING'):
            logger.info('EndPoint is in Creating State')
            is_ready = False
            
        elif(endpointstatus['EndpointProperties']['Status']=='UPDATING'):
            logger.info('EndPoint is in Updating State')
            is_ready = False
            
        elif(endpointstatus['EndpointProperties']['Status']=='DELETING'):
            logger.info('EndPoint is in Deleting State')
            is_ready = True
            
    except Exception as e:
        logger.error("Exception (%s)", e)
        is_ready = True
        return { 'IsComplete': is_ready }
        
    return { 'IsComplete': is_ready } 

    