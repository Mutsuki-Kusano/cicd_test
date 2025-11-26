import json
import os
import sys
import pytest
from moto import mock_aws
import boto3

# functionsモジュールをインポートするためにパスを追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from functions import handler

# 環境変数の設定
os.environ['TABLE_NAME'] = 'test-integration-table'
os.environ['AWS_DEFAULT_REGION'] = 'ap-northeast-1'


@pytest.fixture
def aws_credentials():
    """AWS認証情報のモック"""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'


class TestAPIIntegration:
    """API全体の結合テスト"""

    @mock_aws
    def test_full_crud_workflow(self, aws_credentials):
        """CRUD操作の一連の流れをテスト"""
        
        # handlerのグローバル変数をリセット
        handler.dynamodb = None
        handler.table = None
        
        # DynamoDBテーブルを作成
        dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
        table = dynamodb.create_table(
            TableName='test-integration-table',
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # handlerにテーブルを直接設定
        handler.dynamodb = dynamodb
        handler.table = table
        
        # 1. アイテム作成
        create_event = {
            'httpMethod': 'POST',
            'path': '/items',
            'pathParameters': None,
            'body': json.dumps({'name': '統合テスト商品', 'price': 2000})
        }
        
        create_response = handler.lambda_handler(create_event, None)
        assert create_response['statusCode'] == 201
        
        created_item = json.loads(create_response['body'])
        item_id = created_item['id']
        assert created_item['name'] == '統合テスト商品'
        assert created_item['price'] == 2000
        
        # 2. 作成したアイテムを取得
        get_event = {
            'httpMethod': 'GET',
            'path': f'/items/{item_id}',
            'pathParameters': {'id': item_id},
            'body': None
        }
        
        get_response = handler.lambda_handler(get_event, None)
        assert get_response['statusCode'] == 200
        
        retrieved_item = json.loads(get_response['body'])
        assert retrieved_item['id'] == item_id
        assert retrieved_item['name'] == '統合テスト商品'
        
        # 3. アイテムを更新
        update_event = {
            'httpMethod': 'PUT',
            'path': f'/items/{item_id}',
            'pathParameters': {'id': item_id},
            'body': json.dumps({'name': '更新された商品', 'price': 3000})
        }
        
        update_response = handler.lambda_handler(update_event, None)
        assert update_response['statusCode'] == 200
        
        updated_item = json.loads(update_response['body'])
        assert updated_item['name'] == '更新された商品'
        assert updated_item['price'] == 3000
        
        # 4. 全アイテムを取得
        list_event = {
            'httpMethod': 'GET',
            'path': '/items',
            'pathParameters': None,
            'body': None
        }
        
        list_response = handler.lambda_handler(list_event, None)
        assert list_response['statusCode'] == 200
        
        items = json.loads(list_response['body'])
        assert len(items) >= 1
        
        # 5. アイテムを削除
        delete_event = {
            'httpMethod': 'DELETE',
            'path': f'/items/{item_id}',
            'pathParameters': {'id': item_id},
            'body': None
        }
        
        delete_response = handler.lambda_handler(delete_event, None)
        assert delete_response['statusCode'] == 200
        
        # 6. 削除されたことを確認
        get_deleted_response = handler.lambda_handler(get_event, None)
        assert get_deleted_response['statusCode'] == 404

    @mock_aws
    def test_multiple_items(self, aws_credentials):
        """複数アイテムの作成と取得をテスト"""
        
        # handlerのグローバル変数をリセット
        handler.dynamodb = None
        handler.table = None
        
        # DynamoDBテーブルを作成
        dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
        table = dynamodb.create_table(
            TableName='test-integration-table',
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # handlerにテーブルを直接設定
        handler.dynamodb = dynamodb
        handler.table = table
        
        # 複数アイテムを作成
        for i in range(3):
            create_event = {
                'httpMethod': 'POST',
                'path': '/items',
                'pathParameters': None,
                'body': json.dumps({'name': f'商品{i}', 'price': 1000 * (i + 1)})
            }
            response = handler.lambda_handler(create_event, None)
            assert response['statusCode'] == 201
        
        # 全アイテムを取得
        list_event = {
            'httpMethod': 'GET',
            'path': '/items',
            'pathParameters': None,
            'body': None
        }
        
        list_response = handler.lambda_handler(list_event, None)
        assert list_response['statusCode'] == 200
        
        items = json.loads(list_response['body'])
        assert len(items) == 3
