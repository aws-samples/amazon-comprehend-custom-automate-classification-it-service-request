# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_lambda_event_sources as _lambda_event_sources,
    aws_apigateway as _apigateway,
    aws_events as _events,
    aws_ssm as _ssm,
    aws_ec2 as _ec2,
    aws_events_targets as _event_target,
    aws_s3 as _s3,
    aws_s3_notifications as _aws_s3_notifications,
    aws_sns_subscriptions as _aws_sns_subscriptions,
    aws_sns as _sns,
    aws_sqs as _sqs,
    aws_efs as _efs,
    aws_iam as _iam,
    RemovalPolicy,
    Fn
)
from constructs import Construct

class ExtractLoadTransformEndPointCreateStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, bucket_name: str, vpc: _ec2.Vpc , efs_ap_id: str, file_system_id: str,  comprehendcustomnotificationtopic: _sns.Topic ,  **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        
        bucket = _s3.Bucket.from_bucket_name(self, "ComprehendCustomBucket", bucket_name)
    
        # Retreive  EFS AccessPoint from Previous Stack Creation
        efs_ap =_efs.AccessPoint.from_access_point_attributes(self, "AccessPoint",
           access_point_id=efs_ap_id,
            file_system=_efs.FileSystem.from_file_system_attributes(self, "EFSFileSystem",
             file_system_id=file_system_id,
            security_group=_ec2.SecurityGroup.from_security_group_id(self, "EFSSecurityGroupID", Fn.import_value('EFSSecurityGroupID')) ))
            
        

        comprehend_data_access_role = _iam.Role(self, "ComprehendDataAccessRole",
                                    assumed_by=_iam.ServicePrincipal(
                                    "comprehend.amazonaws.com"),
                                    description="IAM data access role for Comprehend custom")
        
        comprehend_data_access_role.add_to_policy(
            _iam.PolicyStatement(
                effect=_iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:ListBucket",
                    "s3:PutObject"
                    ],
                    resources=[bucket.bucket_arn,bucket.bucket_arn+"/*"]
                
                )
            
            )
            
        #Create ETL Lambda function
        etl_lambda = _lambda.Function(self, "ExtractDatasetLambda",
                                      description="Lambda function for Extracting and Transforming dataset",
                                      runtime=_lambda.Runtime.PYTHON_3_8,
                                      code=_lambda.Code.from_asset(
                                          "./lambdas"),
                                      handler="etl_lambda.lambda_handler",
                                      vpc=vpc,
                                      timeout=Duration.minutes(5),
                                      memory_size=3008,
                                      environment={
                                          "TOPIC_ARN": comprehendcustomnotificationtopic.topic_arn},
                                      filesystem=_lambda.FileSystem.from_efs_access_point(efs_ap, "/mnt/data")
                                      )

        # adding permissions to use S3 bucket, logging, EFS and SNS

        etl_lambda.role.add_to_policy(_iam.PolicyStatement(
                    actions=[
                    "s3:GetObject",
                    "s3:ListBucket",
                    "s3:PutObject",
                    "s3:HeadObject"
                    ],
                    resources=[bucket.bucket_arn,bucket.bucket_arn+"/*"]
            ))
        
        etl_lambda.role.add_to_policy(_iam.PolicyStatement(
            actions=["sns:Publish"],
            resources=[comprehendcustomnotificationtopic.topic_arn]
            ))
            
        s3_notification = _aws_s3_notifications.LambdaDestination(etl_lambda)
        
        # assign notification for the s3 event type (ex: MulitPart Uploads)
        bucket.add_event_notification(_s3.EventType.OBJECT_CREATED_COMPLETE_MULTIPART_UPLOAD,
                                   s3_notification,
                                    _s3.NotificationKeyFilter(prefix="raw_data/"))
                                    
        
        
        # Create Train Classifier Lambda function
        train_classifer_lambda = _lambda.Function(self, "TrainClassifierLambda",
                                                  description="Lambda function for training Comprehend Custom Classifier model",
                                                  runtime=_lambda.Runtime.PYTHON_3_8,
                                                  code=_lambda.Code.from_asset(
                                                      "./lambdas"),
                                                  handler="train_classifier_lambda.lambda_handler",
                                                  vpc=vpc,
                                                  timeout=Duration.minutes(5),
                                                  memory_size=3008,
                                                  environment={
                                                     "BUCKET_NAME": bucket_name,
                                                     "TOPIC_ARN": comprehendcustomnotificationtopic.topic_arn,
                                                     "COMPREHEND_DATA_ACCESS_ROLE_ARN": comprehend_data_access_role.role_arn})

        pass_role_policy = _iam.Policy(self, "PassroleToComprehend", statements=[_iam.PolicyStatement(
            actions=["iam:PassRole"], resources=[comprehend_data_access_role.role_arn])])
        train_classifer_lambda.role.attach_inline_policy(pass_role_policy)

        train_classifer_lambda.role.add_to_policy(_iam.PolicyStatement(
            actions=["comprehend:CreateDocumentClassifier"],
            resources=["arn:aws:comprehend:"+Stack.of(self).region+":"+Stack.of(self).account+":document-classifier/*"]
            ))
        
        train_classifer_lambda.role.add_to_policy(_iam.PolicyStatement(
            actions=["sns:Publish"],
            resources=[comprehendcustomnotificationtopic.topic_arn]
            ))

        comprehendcustomnotificationtopic.add_subscription(_aws_sns_subscriptions.LambdaSubscription(train_classifer_lambda,
             filter_policy={
             "event_type": _sns.SubscriptionFilter.string_filter(
             allowlist=["ETL completed and prepped data uploaded to S3"])})) 
             
             
            
        # Create Extract Comprehend Document Classifier Model Lambda function
        extract_comprehend_model_name_lambda  = _lambda.Function(self, "ExtractComprehendCustomModelARNLambda",
                                      description="Lambda function for  Extracting Comprehend Model ARN",
                                      runtime=_lambda.Runtime.PYTHON_3_8,
                                      code=_lambda.Code.from_asset(
                                          "./lambdas"),
                                      handler="extract_comprehend_model_name_lambda.lambda_handler",
                                      vpc=vpc,
                                      timeout=Duration.minutes(5),
                                      memory_size=3008,
                                      environment={
                                          "TOPIC_ARN": comprehendcustomnotificationtopic.topic_arn},
                                      )

        extract_comprehend_model_name_lambda.role.add_to_policy(_iam.PolicyStatement(
            actions=["comprehend:ListDocumentClassifiers"],
            resources=["*"]
            ))
        extract_comprehend_model_name_lambda.role.add_to_policy(_iam.PolicyStatement(
            actions=["sns:Publish"],
            resources=[comprehendcustomnotificationtopic.topic_arn]
            ))
       
        
        create_s3_notification = _aws_s3_notifications.LambdaDestination(extract_comprehend_model_name_lambda)
        
        #assign notification for the s3 event type (ex: OBJECT_CREATED)
        bucket.add_event_notification(_s3.EventType.OBJECT_CREATED_PUT,
                                      create_s3_notification,
                                      _s3.NotificationKeyFilter(prefix="output_data/", suffix="output.tar.gz"))
       
