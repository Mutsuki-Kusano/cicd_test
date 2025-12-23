# API Gateway + Lambda + DynamoDB CDK プロジェクト（Python版）

## 概要
API Gateway、Lambda、DynamoDBを使用したシンプルなREST APIのCDK構成です。

**複数人開発対応CI/CDパイプライン構築済み** ✅

## ブランチ戦略

### ブランチ構成
- **main**: 本番環境のブランチ
- **v2qa**: 検証環境のブランチ  
- **dev**: 開発環境のブランチ
- **feature/***: 機能開発用の作業ブランチ

### 開発フロー
```
feature/* → dev → v2qa → main
    ↓        ↓      ↓      ↓
  単体テスト  開発環境  検証環境  本番環境
```

## CI/CDパイプライン

### 1. Feature → Dev（単体テスト）
- **トリガー**: feature/* → dev へのプルリクエスト
- **実行内容**: 
  - 単体テスト（カバレッジ80%以上）
  - CDK構文チェック
- **成功時**: 自動でレビュワーにレビュー依頼
- **失敗時**: プルリクエストにコメント、レビュー依頼なし

### 2. Dev → V2QA（結合・システムテスト）
- **トリガー**: dev → v2qa へのプルリクエスト
- **実行内容**:
  - 結合テスト（コンポーネント間連携）
  - システムテスト（エンドツーエンドAPI）
  - CDK構文チェック
- **成功時**: 自動でテストレビュワーにレビュー依頼
- **失敗時**: プルリクエストにコメント、レビュー依頼なし

### 3. 環境別自動デプロイ
- **dev環境**: devブランチへのプッシュ時
- **v2qa環境**: v2qaブランチへのプッシュ時  
- **本番環境**: mainブランチへのプッシュ時（承認必須）

## 複数人開発の設定

### 必要なGitHub Secrets
各環境用のIAMロールARNを設定：
- `AWS_DEV_ROLE_ARN`: 開発環境用
- `AWS_V2QA_ROLE_ARN`: 検証環境用
- `AWS_PROD_ROLE_ARN`: 本番環境用

### GitHub Environments設定
1. Settings → Environments で以下を作成：
   - `development` (dev環境用)
   - `v2qa` (検証環境用)
   - `production` (本番環境用、承認必須)

### チームメンバーの追加
ワークフローファイルの以下の箇所を更新：

#### レビュワー設定の注意点
プルリクエスト作成者は自分自身にレビューを依頼できないため、ワークフローでは自動的に作成者を除外します。

**個人開発の場合:**
```yaml
# .github/workflows/feature-to-dev.yml
const allReviewers = []; // 空配列にしておく
```

**チーム開発の場合:**
```yaml
# .github/workflows/feature-to-dev.yml
const allReviewers = ['alice', 'bob', 'charlie']; // 実際のGitHubユーザー名

# .github/workflows/dev-to-v2qa.yml  
const allReviewers = ['qa-member1', 'qa-member2']; // QAチームメンバー
```

ワークフローは以下の動作をします：
- ✅ 利用可能なレビュワーがいる場合：自動でレビュー依頼を送信
- ⚠️ 利用可能なレビュワーがいない場合：手動指定を促すコメントを投稿

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

### テスト構成
プロジェクトでは3段階のテスト体制を採用しています：

1. **単体テスト** (`tests/unit/`): 個別の関数・クラスのテスト
2. **結合テスト** (`tests/integration/`): コンポーネント間の連携テスト
3. **システムテスト** (`tests/system/`): エンドツーエンドのAPIテスト

### ローカルでのテスト実行

```bash
# テスト用依存関係のインストール
pip install -r requirements-dev.txt

# 単体テストの実行
pytest tests/unit/ -v

# 結合テストの実行
pytest tests/integration/ -v

# システムテストの実行
pytest tests/system/ -v

# 全テストの実行（カバレッジ付き）
pytest -v --cov=functions --cov-report=term-missing

# テストタイプ別実行（マーカー使用）
pytest -m unit -v      # 単体テストのみ
pytest -m integration -v  # 結合テストのみ  
pytest -m system -v    # システムテストのみ
```

### テストの詳細

#### 単体テスト
- Lambda関数の各メソッドを個別にテスト
- モックを使用してAWS依存関係を排除
- カバレッジ80%以上を要求

#### 結合テスト
- DynamoDBとLambda関数の連携をテスト
- motoライブラリでAWSサービスをモック
- CRUD操作の一連の流れを検証

#### システムテスト
- APIエンドポイントのエンドツーエンドテスト
- HTTPリクエスト/レスポンスの検証
- エラーハンドリングとパフォーマンステスト
- 実際のAPI呼び出しをモック化して実行

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

詳細な手順は `docs/aws-iam-setup.md` を参照してください。

**簡単な手順：**
1. AWSコンソール → IAM → IDプロバイダー → プロバイダーを追加
2. OpenID Connect、URL: `https://token.actions.githubusercontent.com`
3. IAMロール作成（信頼ポリシーでGitHubリポジトリを指定）
4. 必要な権限をロールに付与
5. ロールのARNをGitHub Secretsに設定

## プロジェクト構造

```
cicd_test/
├── .github/workflows/          # GitHub Actionsワークフロー
│   ├── feature-to-dev.yml     # 単体テスト（feature→dev PR時）
│   ├── dev-to-v2qa.yml        # 結合・システムテスト（dev→v2qa PR時）
│   ├── deploy-dev.yml         # 開発環境デプロイ
│   ├── deploy-v2qa.yml        # 検証環境デプロイ
│   └── deploy-prod.yml        # 本番環境デプロイ
├── docs/                      # ドキュメント
│   └── aws-iam-setup.md      # AWS IAM設定ガイド
├── functions/                 # Lambda関数
│   ├── __init__.py
│   └── handler.py            # メインのLambda関数
├── stacks/                   # CDKスタック定義
│   ├── __init__.py
│   └── api_stack.py         # API Gateway + Lambda + DynamoDB
├── tests/                   # テストファイル
│   ├── unit/               # 単体テスト
│   │   └── test_handler.py
│   ├── integration/        # 結合テスト
│   │   └── test_api_integration.py
│   └── system/            # システムテスト
│       └── test_api_system.py
├── app.py                 # CDKアプリのエントリーポイント
├── cdk.json              # CDK設定
├── pytest.ini           # pytest設定
├── requirements.txt      # 本番依存関係
└── requirements-dev.txt  # 開発・テスト依存関係
```
## 開発フロー


### 基本的な開発手順

1. **ブランチ作成**: `git checkout -b feature/new-feature`
2. **コード作成・修正**: 機能実装とテスト作成
3. **ローカルテスト**: `pytest tests/unit/ -v`
4. **コミット**: `git commit -m "Add new feature"`
5. **プッシュ**: `git push origin feature/new-feature`
6. **プルリクエスト作成** → 単体テスト自動実行
7. **レビュー・承認**
8. **devブランチへマージ** → 開発環境デプロイ
9. **v2qaへのプルリクエスト** → 結合・システムテスト自動実行
10. **テストレビュー・承認**
11. **v2qaブランチへマージ** → 検証環境デプロイ
12. **mainへのプルリクエスト** → 本番環境デプロイ

### テスト戦略

| テストレベル | 実行タイミング | 目的 | 使用技術 |
|-------------|---------------|------|----------|
| **単体テスト** | feature→dev PR | 個別機能の動作確認 | pytest + mock |
| **結合テスト** | dev→v2qa PR | コンポーネント連携確認 | pytest + moto |
| **システムテスト** | dev→v2qa PR | エンドツーエンド確認 | pytest + requests |

### 品質ゲート

- **単体テスト**: カバレッジ80%以上
- **結合テスト**: 全CRUD操作の成功
- **システムテスト**: API呼び出しとエラーハンドリング
- **CDK構文チェック**: 全環境でのsynth成功