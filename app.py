#!/usr/bin/env python3
import os
import aws_cdk as cdk
from stacks.api_stack import ApiStack

app = cdk.App()

# アカウント情報を環境変数から取得、テスト用のフォールバック値を設定
account = (
    os.getenv('CDK_DEFAULT_ACCOUNT') or 
    os.getenv('AWS_ACCOUNT_ID') or
    "123456789012"  # テスト用のダミーアカウントID
)
region = os.getenv('CDK_DEFAULT_REGION', 'ap-northeast-1')

# デバッグ情報を出力
print(f"Using account: {account}")
print(f"Using region: {region}")

env = cdk.Environment(account=account, region=region)

ApiStack(app, "ApiStack", env=env)

app.synth()
