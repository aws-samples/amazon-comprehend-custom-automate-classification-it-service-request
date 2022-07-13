# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    Duration,
    Stack,
    aws_ec2 as _ec2,
    aws_efs as _efs,
    RemovalPolicy,
    CfnOutput,
    Names
)

from constructs import Construct

class EFSStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: _ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        
        # The code that defines your stack goes here
        
        # Create Elastic File System (EFS)       
        efs = _efs.FileSystem(self, "ComprehendCustomEfs",
                              vpc=vpc,
                              performance_mode=_efs.PerformanceMode.GENERAL_PURPOSE,
                              removal_policy=RemovalPolicy.DESTROY)
                              
   
        # Create EFS Access Points for Lambda Mounts
        efs_ap = efs.add_access_point("AccessPoint",
                                      create_acl=_efs.Acl(
                                      owner_gid="1001", owner_uid="1001", permissions="750"),
                                      path="/mnt/data",
                                      posix_user=_efs.PosixUser(gid="1001", uid="1001"))
                                      
        efs_security_group_list=efs.connections.security_groups
        
        
        # Assign instance variables
        
        self.efs_ap_id=efs_ap.access_point_id
        self.file_system_id=efs.file_system_id
        CfnOutput(self, "EFSSecurityGroupID", 
            value=efs_security_group_list[0].security_group_id,
            export_name="EFSSecurityGroupID"
        )
    
        