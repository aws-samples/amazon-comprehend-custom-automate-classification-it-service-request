# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import requests
import json

#Refer to https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html for setting the correct AWS credentials parameters
session = boto3.Session()
credentials = session.get_credentials()

raw_data="""

Spark is a unified analytics engine for large-scale data processing. It provides high-level APIs in Scala, Java, Python, and R, and an optimized engine that supports 
general computation graphs for data analysis. It also supports a rich set of higher-level tools including Spark SQL for SQL and DataFrames, pandas API on Spark for 
pandas workloads, MLlib for machine learning, GraphX for graph processing, and Structured Streaming for stream processing.

"""

#<restapi-id> to be updated based on the REST API ID value retreived from deploying the APIGWInferenceStack
#For example  Rest API URL when deploying in us-east-2
restapi = "https://<restapi-id>.execute-api.us-east-2.amazonaws.com/prod/invokecomprehendV1"

formatted_data = " ".join(raw_data.split()).replace ('"', '\\"')

json_data=json.dumps({"Text": formatted_data})


headers = {'Content-Type': 'application/json'}

def signed_request(url, data, params=None, headers=None):
    request = AWSRequest(method="POST", url=url, data=data, headers=headers)
    #Update <AWS-REGION> to the AWS Region where the REST API is deployed
    SigV4Auth(credentials, "execute-api", "<AWS-REGION>").add_auth(request)
    return requests.post( url=url, headers=dict(request.headers), data=data).text

def main():

    response = signed_request(url=restapi, data=json_data, headers=headers)
    json_object = json.loads(response)
    print(json.dumps(json_object, indent=2))

if __name__ == "__main__":
    main()
