# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    Duration,
    Stack,
    aws_sns as _sns,
    aws_sns_subscriptions as _aws_sns_subscriptions,
    CfnParameter
    
)

from constructs import Construct

class SNSStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        email_address = CfnParameter(self, "emailaddressarnnotification", description="Notification Topic for Status Updates")
        
        # The code that defines your stack goes here
        
        # Create SNS Topic and subscription
        comprehendcustomnotificationtopic = _sns.Topic(self, "ComprehendCustomNotificationTopic",
                           display_name="ComprehendCustomNotificationTopic",
                           topic_name="ComprehendCustomNotificationTopic"
                           )
                         
        comprehendcustomnotificationtopic.add_subscription(_aws_sns_subscriptions.EmailSubscription(email_address.value_as_string))

        
        # Assign instance variables
        
        self.comprehendcustomnotificationtopic=comprehendcustomnotificationtopic
        
        