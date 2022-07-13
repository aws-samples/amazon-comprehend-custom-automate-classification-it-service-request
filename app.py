# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

#!/usr/bin/env python3
import os

import aws_cdk as cdk


from vpc_stack.vpc_stack import VPCStack
from efs_stack.efs_stack import EFSStack
from s3_stack.s3_stack import S3Stack
from sns_stack.sns_stack import SNSStack
from extract_load_transform_endpointcreate_stack.extract_load_transform_endpointcreate_stack import ExtractLoadTransformEndPointCreateStack
from apigateway_inference_stack.apigateway_inference_stack import APIGWInferenceStack



app = cdk.App()

vpcStack = VPCStack(app, "VPCStack", env = cdk.Environment(account=os.environ["CDK_DEFAULT_ACCOUNT"], region=os.environ["CDK_DEFAULT_REGION"]))
efsStack = EFSStack(app, "EFSStack", vpcStack.vpc, env = cdk.Environment(account=os.environ["CDK_DEFAULT_ACCOUNT"], region=os.environ["CDK_DEFAULT_REGION"]))
s3Stack = S3Stack(app, "S3Stack", env = cdk.Environment(account=os.environ["CDK_DEFAULT_ACCOUNT"], region=os.environ["CDK_DEFAULT_REGION"]))
snsStack = SNSStack(app, "SNSStack", env = cdk.Environment(account=os.environ["CDK_DEFAULT_ACCOUNT"], region=os.environ["CDK_DEFAULT_REGION"]))
etlendpointcreateStack=ExtractLoadTransformEndPointCreateStack(app, "ExtractLoadTransformEndPointCreateStack", 
                                        bucket_name=s3Stack.bucket_name,
                                        vpc=vpcStack.vpc,
                                        efs_ap_id=efsStack.efs_ap_id,
                                        file_system_id=efsStack.file_system_id,
                                        comprehendcustomnotificationtopic=snsStack.comprehendcustomnotificationtopic,
                                        env = cdk.Environment(account=os.environ["CDK_DEFAULT_ACCOUNT"], region=os.environ["CDK_DEFAULT_REGION"]))
apigwinferenceStack = APIGWInferenceStack(app, "APIGWInferenceStack", vpc=vpcStack.vpc, env = cdk.Environment(account=os.environ["CDK_DEFAULT_ACCOUNT"], region=os.environ["CDK_DEFAULT_REGION"]))

app.synth()
