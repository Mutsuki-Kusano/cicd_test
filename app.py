#!/usr/bin/env python3
import os
import aws_cdk as cdk
from stacks.api_stack import ApiStack

app = cdk.App()

# アカウント情報を複数の方法で取得を試行
account = (
    os.getenv('CDK_DEFAULT_ACCOUNT') or 
    os.getenv('AWS_ACCOUNT_ID') or
    app.node.try_get_context('account')
)

region = (
    os.getenv('CDK_DEFAULT_REGION') or 
    os.getenv('AWS_DEFAULT_REGION') or
    'ap-northeast-1'
)

# デバッグ情報を出力
print(f"Using account: {account}")
print(f"Using region: {region}")

if not account:
    raise ValueError("AWS account ID must be provided via CDK_DEFAULT_ACCOUNT or AWS_ACCOUNT_ID environment variable")

env = cdk.Environment(account=account, region=region)

ApiStack(app, "ApiStack", env=env)

app.synth()
