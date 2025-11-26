# API Gateway + Lambda + DynamoDB CDK プロジェクト（Python版）

## 概要
API Gateway、Lambda、DynamoDBを使用したシンプルなREST APIのCDK構成です。

## 前提条件
- Python 3.8以上
- AWS CLI設定済み
- AWS SSO設定済み（プロファイル: pfdev）
- AWS CDK CLI（`npm install -g aws-cdk`）

## セットアップ

1. AWS SSOログイン：
```bash
aws sso login --profile pfdev
```

2. 仮想環境の作成と有効化：
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. 依存関係のインストール：
```bash
pip install -r requirements.txt
```

4. CDKのブートストラップ（初回のみ）：
```bash
cdk bootstrap
```

## デプロイ

```bash
cdk deploy
```

デプロイ後、API GatewayのURLが出力されます。

**注意**: SSOセッションが切れた場合は、再度`aws sso login --profile pfdev`を実行してください。

## API エンドポイント

- `GET /items` - 全アイテム取得
- `POST /items` - アイテム作成
- `GET /items/{id}` - 単一アイテム取得
- `PUT /items/{id}` - アイテム更新
- `DELETE /items/{id}` - アイテム削除

## テスト例

```bash
# アイテム作成
curl -X POST https://your-api-url/prod/items -H "Content-Type: application/json" -d "{\"name\":\"テストアイテム\",\"description\":\"説明\"}"

# 全アイテム取得
curl https://your-api-url/prod/items
```

## クリーンアップ

```bash
cdk destroy
```

## テスト

### ローカルでのテスト実行

```bash
# テスト用依存関係のインストール
pip install pytest pytest-cov moto

# 単体テストの実行
pytest tests/unit/ -v

# 結合テストの実行
pytest tests/integration/ -v

# 全テストの実行（カバレッジ付き）
pytest -v --cov=functions --cov-report=term-missing
```

## CI/CD パイプライン

### GitHub Actionsワークフロー

1. **プルリクエスト作成時** (`.github/workflows/pr-test.yml`)
   - 単体テストの実行
   - CDK構文チェック

2. **mainブランチへのマージ時** (`.github/workflows/deploy.yml`)
   - 結合テストの実行
   - AWSへの自動デプロイ

### GitHub Secretsの設定

デプロイを有効にするには、以下のシークレットを設定してください：

1. GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」
2. 「New repository secret」をクリック
3. 以下のシークレットを追加：
   - `AWS_ROLE_ARN`: GitHub ActionsからAssumeするIAMロールのARN

### IAMロールの作成（OIDC）

```bash
# AWS CLIでOIDCプロバイダーとロールを作成
# 詳細はAWS公式ドキュメントを参照
```

## 開発フロー

1. ブランチ作成: `git checkout -b feature/new-feature`
2. コード作成・修正
3. コミット: `git commit -m "Add new feature"`
4. プッシュ: `git push origin feature/new-feature`
5. プルリクエスト作成 → 単体テスト自動実行
6. レビュー・承認
7. mainブランチへマージ → 結合テスト・デプロイ自動実行
