#!/usr/bin/env python3
import os
import aws_cdk as cdk
from stacks.api_stack import ApiStack

app = cdk.App()

# 環境情報を取得
environment = os.getenv('ENVIRONMENT', 'dev')
account = os.getenv('CDK_DEFAULT_ACCOUNT') or os.getenv('AWS_ACCOUNT_ID')
region = os.getenv('CDK_DEFAULT_REGION', 'ap-northeast-1')

# デバッグ情報を出力
print(f"Using account: {account}")
print(f"Using region: {region}")
print(f"Environment: {environment}")

if not account:
    raise ValueError("AWS account ID must be provided via CDK_DEFAULT_ACCOUNT or AWS_ACCOUNT_ID environment variable")

env = cdk.Environment(account=account, region=region)

# 環境別にスタックを作成
if environment == 'prod':
    ApiStack(app, "ApiStack-Prod", env=env, environment='prod')
elif environment == 'v2qa':
    ApiStack(app, "ApiStack-V2QA", env=env, environment='v2qa')
elif environment == 'dev':
    ApiStack(app, "ApiStack-Dev", env=env, environment='dev')
else:
    # デフォルト（テスト用）
    ApiStack(app, "ApiStack", env=env, environment='test')

app.synth()
