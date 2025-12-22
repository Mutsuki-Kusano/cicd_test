#!/usr/bin/env python3
import os
import aws_cdk as cdk
from stacks.api_stack import ApiStack

app = cdk.App()

# アカウント情報を環境変数から取得
account = os.getenv('CDK_DEFAULT_ACCOUNT') or os.getenv('AWS_ACCOUNT_ID')
region = os.getenv('CDK_DEFAULT_REGION', 'ap-northeast-1')

# デバッグ情報を出力
print(f"Using account: {account}")
print(f"Using region: {region}")

if not account:
    raise ValueError("AWS account ID must be provided via CDK_DEFAULT_ACCOUNT or AWS_ACCOUNT_ID environment variable")

env = cdk.Environment(account=account, region=region)

ApiStack(app, "ApiStack", env=env)

app.synth()
