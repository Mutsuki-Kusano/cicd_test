# GitHub Actions用IAMロール作成ガイド

## 概要

GitHub ActionsからAWSリソースにアクセスするためのIAMロールを作成します。OIDC（OpenID Connect）を使用することで、長期間有効なアクセスキーを使わずに安全にAWSにアクセスできます。

## 手順1: OIDCプロバイダーの作成

### AWSコンソールでの作成

1. **IAMコンソールにアクセス**
   - AWSコンソール → IAM → 「IDプロバイダー」

2. **プロバイダーを追加**
   - 「プロバイダーを追加」をクリック
   - プロバイダーのタイプ: `OpenID Connect`
   - プロバイダーのURL: `https://token.actions.githubusercontent.com`
   - 対象者: `sts.amazonaws.com`
   - 「プロバイダーを追加」をクリック

### AWS CLIでの作成

```bash
# OIDCプロバイダーの作成
aws iam create-open-id-connect-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

## 手順2: IAMロールの作成

### 信頼ポリシーの作成

`github-actions-trust-policy.json`ファイルを作成：

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                },
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_USERNAME/YOUR_REPO_NAME:*"
                }
            }
        }
    ]
}
```

**重要**: 以下を実際の値に置き換えてください：
- `YOUR_ACCOUNT_ID`: AWSアカウントID（12桁の数字）
- `YOUR_GITHUB_USERNAME`: GitHubユーザー名
- `YOUR_REPO_NAME`: リポジトリ名

### 権限ポリシーの作成

CDKデプロイに必要な権限を定義した`github-actions-permissions.json`：

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cloudformation:*",
                "s3:*",
                "iam:*",
                "lambda:*",
                "apigateway:*",
                "dynamodb:*",
                "logs:*",
                "sts:AssumeRole"
            ],
            "Resource": "*"
        }
    ]
}
```

### AWS CLIでロール作成

```bash
# 1. IAMロールの作成
aws iam create-role \
    --role-name GitHubActionsRole \
    --assume-role-policy-document file://github-actions-trust-policy.json

# 2. 権限ポリシーの作成
aws iam create-policy \
    --policy-name GitHubActionsPolicy \
    --policy-document file://github-actions-permissions.json

# 3. ロールにポリシーをアタッチ
aws iam attach-role-policy \
    --role-name GitHubActionsRole \
    --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/GitHubActionsPolicy
```

### AWSコンソールでロール作成

1. **IAMコンソール → ロール → ロールを作成**

2. **信頼されたエンティティタイプ**
   - 「ウェブアイデンティティ」を選択
   - アイデンティティプロバイダー: `token.actions.githubusercontent.com`
   - Audience: `sts.amazonaws.com`

3. **条件の追加**
   - 条件キー: `token.actions.githubusercontent.com:sub`
   - 演算子: `StringLike`
   - 値: `repo:YOUR_GITHUB_USERNAME/YOUR_REPO_NAME:*`

4. **権限の追加**
   - 既存のポリシーをアタッチするか、上記のカスタムポリシーを作成

5. **ロール名**
   - 名前: `GitHubActionsRole`
   - 説明: `Role for GitHub Actions to deploy CDK`

## 手順3: GitHub Secretsの設定

1. **GitHubリポジトリ → Settings → Secrets and variables → Actions**

2. **New repository secret**
   - Name: `AWS_ROLE_ARN`
   - Value: `arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubActionsRole`

## 手順4: GitHub Actionsワークフローの更新

`.github/workflows/deploy.yml`を以下のように更新：

```yaml
name: Deploy to AWS

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    permissions:
      id-token: write
      contents: read
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ap-northeast-1

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Install CDK
        run: npm install -g aws-cdk

      - name: CDK Deploy
        run: cdk deploy --require-approval never
```

## セキュリティのベストプラクティス

### 1. 最小権限の原則

本番環境では、必要最小限の権限のみを付与：

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cloudformation:CreateStack",
                "cloudformation:UpdateStack",
                "cloudformation:DescribeStacks",
                "cloudformation:DescribeStackEvents",
                "s3:GetObject",
                "s3:PutObject",
                "lambda:CreateFunction",
                "lambda:UpdateFunctionCode",
                "apigateway:POST",
                "apigateway:PUT",
                "dynamodb:CreateTable",
                "dynamodb:DescribeTable"
            ],
            "Resource": [
                "arn:aws:cloudformation:ap-northeast-1:YOUR_ACCOUNT_ID:stack/ApiStack/*",
                "arn:aws:s3:::cdk-*",
                "arn:aws:lambda:ap-northeast-1:YOUR_ACCOUNT_ID:function:ApiStack-*",
                "arn:aws:apigateway:ap-northeast-1::/restapis/*",
                "arn:aws:dynamodb:ap-northeast-1:YOUR_ACCOUNT_ID:table/ApiStack-*"
            ]
        }
    ]
}
```

### 2. 条件の制限

特定のブランチやタグからのみアクセスを許可：

```json
{
    "StringLike": {
        "token.actions.githubusercontent.com:sub": [
            "repo:YOUR_GITHUB_USERNAME/YOUR_REPO_NAME:ref:refs/heads/main",
            "repo:YOUR_GITHUB_USERNAME/YOUR_REPO_NAME:ref:refs/tags/*"
        ]
    }
}
```

## トラブルシューティング

### よくあるエラー

1. **`AssumeRoleFailure`**
   - 信頼ポリシーの条件を確認
   - リポジトリ名、ユーザー名が正しいか確認

2. **`AccessDenied`**
   - 権限ポリシーを確認
   - 必要な権限が付与されているか確認

3. **`InvalidIdentityToken`**
   - OIDCプロバイダーが正しく作成されているか確認
   - Audienceが`sts.amazonaws.com`になっているか確認

### デバッグ方法

GitHub Actionsのログで以下を確認：

```yaml
- name: Debug AWS Identity
  run: |
    aws sts get-caller-identity
    aws sts get-session-token
```

## まとめ

この設定により、GitHub ActionsからAWSに安全にアクセスできるようになります。長期間有効なアクセスキーを使用せず、一時的な認証情報のみを使用するため、セキュリティが向上します。