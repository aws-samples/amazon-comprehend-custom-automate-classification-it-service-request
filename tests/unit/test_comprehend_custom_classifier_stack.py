# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import aws_cdk as core
import aws_cdk.assertions as assertions

from comprehend_custom_classifier.comprehend_custom_classifier_stack import ComprehendCustomClassifierStack

# example tests. To run these tests, uncomment this file along with the example
# resource in comprehend_custom_classifier/comprehend_custom_classifier_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ComprehendCustomClassifierStack(app, "comprehend-custom-classifier")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
