# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    Duration,
    Stack,
    aws_ec2 as _ec2,
    aws_iam as _iam

)

from constructs import Construct

class VPCStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # The code that defines your stack goes here
        
        # Create VPC and Private Subnets
        vpc = _ec2.Vpc(self, "CompehendVPCStack",
                       cidr="10.0.2.0/24",
                       max_azs=2,
                       enable_dns_support=True,
                       enable_dns_hostnames=True,
                       subnet_configuration=[
                           _ec2.SubnetConfiguration(
                               name="Private",
                               subnet_type=_ec2.SubnetType.PRIVATE_ISOLATED,
                               cidr_mask=26
                              )])
        
        # Create Lambda VPC EndPoint                     
        lambda_endpoint = _ec2.InterfaceVpcEndpoint(self, "LambdaInterfaceEndpoint",
                                                    vpc=vpc,
                                                    lookup_supported_azs=True,
                                                    service=_ec2.InterfaceVpcEndpointAwsService("lambda"))
        lambda_endpoint.node.add_dependency(vpc)
        
        # Create S3 VPC EndPoint 

        s3_endpoint = vpc.add_gateway_endpoint("S3Endpoint",
                                               service=_ec2.GatewayVpcEndpointAwsService.S3,
                                               subnets=[_ec2.SubnetSelection(
                                               subnet_type=_ec2.SubnetType.PRIVATE_ISOLATED)]
                                               )
        s3_endpoint.node.add_dependency(vpc)
        
        
        # Create Comprehend VPC EndPoint 
        comprehend_endpoint = _ec2.InterfaceVpcEndpoint(self, "ComprehendInterfaceEndpoint",
                                                        vpc=vpc,
                                                        lookup_supported_azs=True,
                                                        service=_ec2.InterfaceVpcEndpointAwsService("comprehend"))
        
        comprehend_endpoint.node.add_dependency(vpc)
        
        stepfunc_endpoint = _ec2.InterfaceVpcEndpoint(self, "StepFuncInterfaceEndpoint",
                                                        vpc=vpc,
                                                        lookup_supported_azs=True,
                                                        service=_ec2.InterfaceVpcEndpointAwsService("states"))
        
        stepfunc_endpoint.node.add_dependency(vpc)
        
        
        # Creare SNS VPC EndPoint
        sns_endpoint = _ec2.InterfaceVpcEndpoint(self, "SNSInterfaceEndpoint",
                                                 vpc=vpc,
                                                 lookup_supported_azs=True,
                                                 service=_ec2.InterfaceVpcEndpointAwsService("sns"))
        sns_endpoint.node.add_dependency(vpc)
        
        # Create SNS Topic and subscription
        
        
        # Assign instance variables
        self.vpc=vpc
        
        