# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_ec2 as _ec2,
    aws_apigateway as _apigateway,
    aws_iam as _iam,
    custom_resources as _cr,
    CfnParameter,
    CfnOutput,
    CustomResource,
    RemovalPolicy
   )
from constructs import Construct




class APIGWInferenceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: _ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        
        documentclassifierarn = CfnParameter(self, "documentclassifierarn", description="DocumentClassifierARN")
        
        comprehend_endpoint_lambda  = _lambda.Function(self, "CreateComprehendEndPointLambda",
                                      description="Lambda function for Creating Comprehend EndPoint",
                                      runtime=_lambda.Runtime.PYTHON_3_8,
                                      code=_lambda.Code.from_asset(
                                          "./lambdas"),
                                      handler="comprehend_endpoint_lambda.on_event",
                                      vpc=vpc,
                                      timeout=Duration.minutes(5),
                                      memory_size=3008
                                      )
                                      
        comprehend_endpoint_lambda.role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name(
            "AmazonS3FullAccess"))
        comprehend_endpoint_lambda.role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name(
            "ComprehendFullAccess"))
        comprehend_endpoint_lambda.role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name(
            "CloudWatchLogsFullAccess"))
        comprehend_endpoint_lambda.role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name(
           "AmazonSNSFullAccess"))
           
        verify_comprehend_endpoint  = _lambda.Function(self, "VerifyComprehendEndPointLambda",
                                      description="Lambda function for Verifying Comprehend EndPoint",
                                      runtime=_lambda.Runtime.PYTHON_3_8,
                                      code=_lambda.Code.from_asset(
                                          "./lambdas"),
                                      handler="verify_comprehend_endpoint_lambda.is_complete",
                                      vpc=vpc,
                                      timeout=Duration.minutes(5),
                                      memory_size=3008
                                      )
                                      
        verify_comprehend_endpoint.role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name(
            "AmazonS3FullAccess"))
        verify_comprehend_endpoint.role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name(
            "ComprehendFullAccess"))
        verify_comprehend_endpoint.role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name(
            "CloudWatchLogsFullAccess"))
        verify_comprehend_endpoint.role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name(
           "AmazonSNSFullAccess"))
           
        # Create Lambda backed Custom provider
        custom_provider = _cr.Provider(self, "ComprehendEndPointProvider",
            on_event_handler=comprehend_endpoint_lambda,
            is_complete_handler=verify_comprehend_endpoint,  # optional async "waiter"
            query_interval=Duration.seconds(5),
            vpc=vpc
            )
            
        # Create Custom Resource - Comprehend EndPoint
        custom_resource=CustomResource(self, "ComprehendEndPointResource", 
                properties={
                "documentclassifierarn": documentclassifierarn
                },
                removal_policy=RemovalPolicy.DESTROY,
                service_token=custom_provider.service_token
                )
                
    
        # The code that defines your stack goes here
        invoke_comprehend_lambda  = _lambda.Function(self, "InvokeComprehendLambda",
                                    description="Lambda function for invoking comprehend endpoint for Inference",
                                      runtime=_lambda.Runtime.PYTHON_3_8,
                                      code=_lambda.Code.from_asset(
                                          "./lambdas"),
                                      handler="invoke_comprehend_lambda.lambda_handler",
                                      vpc=vpc,
                                      timeout=Duration.minutes(5),
                                      memory_size=3008,
                                     environment={
                                         "ENDPOINT_ARN": custom_resource.get_att_string('EndpointArn')
                                          }
                                      )
                                      
        
        invoke_comprehend_lambda.role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name(
            "AmazonS3FullAccess"))
        invoke_comprehend_lambda.role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name(
            "ComprehendFullAccess"))
        invoke_comprehend_lambda.role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name(
            "CloudWatchLogsFullAccess"))
     
            
        restapi = _apigateway.RestApi(self, "ComprehendAPIInvokeV1", 
                                            description='Invoke Comprehend API for Classification' , 
                                            endpoint_configuration=_apigateway.EndpointConfiguration(
                                                types=[_apigateway.EndpointType.REGIONAL])
                                            )
                                            
        restapiresource = restapi.root.add_resource("invokecomprehendV1")
        
        restapiresource.add_method("POST", _apigateway.LambdaIntegration(invoke_comprehend_lambda, proxy=False,
                                    integration_responses=[_apigateway.IntegrationResponse(status_code="200")]), 
                                    authorization_type=_apigateway.AuthorizationType.IAM, 
                                    method_responses=[_apigateway.MethodResponse(status_code="200")
                                    ])
                                    
        CfnOutput(self, "Comprehend-CustomClassfier-InvokeAPI", 
            value=f"https://{restapi.rest_api_id}.execute-api.{restapi.env.region}.amazonaws.com/{restapi.deployment_stage.stage_name}{restapiresource.path}"
        )
       
      

