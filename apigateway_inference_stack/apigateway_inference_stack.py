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
        
        # Create Comprehend Endpoint Lambda function that creates, updates and deletes the Amazon Comprehend endpoint based on your stack lifecycle events
        # cdk deploy triggers this Lambda function to create the Amazon Comprehend endpoint
        # cdk destroy triggers this Lambda function to delete the Amazon Comprehend endpoint
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
                      
        comprehend_endpoint_lambda.role.add_to_policy(_iam.PolicyStatement(
            actions=["comprehend:CreateEndpoint","comprehend:DeleteEndpoint","comprehend:UpdateEndpoint"],
            resources=["arn:aws:comprehend:"+Stack.of(self).region+":"+Stack.of(self).account+":document-classifier-endpoint/*", "arn:aws:comprehend:"+Stack.of(self).region+":"+Stack.of(self).account+":document-classifier/*"]
           
            ))

        # Create Verify Comprehend Endpoint Lambda function that acts as an asynchronous handler for Custom provider framework . This  enables operations that require a long waiting period for a resource, which can exceed the AWS Lambda timeout
        verify_comprehend_endpoint_lambda  = _lambda.Function(self, "VerifyComprehendEndPointLambda",
                                      description="Lambda function for Verifying Comprehend EndPoint",
                                      runtime=_lambda.Runtime.PYTHON_3_8,
                                      code=_lambda.Code.from_asset(
                                          "./lambdas"),
                                      handler="verify_comprehend_endpoint_lambda.is_complete",
                                      vpc=vpc,
                                      timeout=Duration.minutes(5),
                                      memory_size=3008
                                      )
        
        verify_comprehend_endpoint_lambda.role.add_to_policy(_iam.PolicyStatement(
            actions=["comprehend:DescribeEndpoint"],
            resources=["arn:aws:comprehend:"+Stack.of(self).region+":"+Stack.of(self).account+":document-classifier-endpoint/*"]
            ))

           
        # Create Lambda backed Custom Resource provider using the Provider Framework
        custom_provider = _cr.Provider(self, "ComprehendEndPointProvider",
            on_event_handler=comprehend_endpoint_lambda,
            is_complete_handler=verify_comprehend_endpoint_lambda,  # optional async "waiter"
            query_interval=Duration.seconds(5),
            vpc=vpc
            )
            
        # Create Custom Resource using the Provider Framework . Here the custom resource is the Amazon Comprehend EndPoint
        custom_resource=CustomResource(self, "ComprehendEndPointResource", 
                properties={
                "documentclassifierarn": documentclassifierarn
                },
                removal_policy=RemovalPolicy.DESTROY,
                service_token=custom_provider.service_token
                )
                
    
        # Create Invoke Comprehend Lambda functions which is to invoke the trained custom classifier model
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
                                      
        
        invoke_comprehend_lambda.role.add_to_policy(_iam.PolicyStatement(
            actions=["comprehend:ClassifyDocument","comprehend:DescribeEndpoint"],
            resources=["arn:aws:comprehend:"+Stack.of(self).region+":"+Stack.of(self).account+":document-classifier-endpoint/*"]
            ))
        
 
     
        # Create API Gateway REST API secured by IAM authorizer 
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
       
      

