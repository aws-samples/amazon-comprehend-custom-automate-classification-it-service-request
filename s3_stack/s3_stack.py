# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    Duration,
    Stack,
    aws_s3 as _s3,
    RemovalPolicy,
    Names
)

from constructs import Construct

class S3Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        
        # Create S3 Bucket
        bucket_name = "comprehendcustom" + "-" + \
           str(self.account) + "-" + str(self.region) + "-" + construct_id.lower()
           
        bucket = _s3.Bucket(self, "ComprehendCustomBucket",
                           bucket_name=bucket_name,
                           removal_policy=RemovalPolicy.DESTROY,
                           block_public_access=_s3.BlockPublicAccess.BLOCK_ALL,
                           encryption=_s3.BucketEncryption.S3_MANAGED,
                           versioned=True,
                           auto_delete_objects=True)
        
        
        # Assign instance variables
        
        
        
        self.bucket_name=bucket_name
        
        