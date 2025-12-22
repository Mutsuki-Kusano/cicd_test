#!/usr/bin/env python3
import os
import aws_cdk as cdk
from stacks.api_stack import ApiStack

app = cdk.App()

# GitHub Actions環境では環境変数から取得、ローカルでは自動取得
env = cdk.Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT') or os.getenv('AWS_ACCOUNT_ID'),
    region=os.getenv('CDK_DEFAULT_REGION', 'ap-northeast-1')
)

ApiStack(app, "ApiStack", env=env)

app.synth()
