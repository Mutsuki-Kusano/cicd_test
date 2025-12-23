import json
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# 環境変数を先に設定
os.environ['TABLE_NAME'] = 'test-table'
os.environ['AWS_DEFAULT_REGION'] = 'ap-northeast-1'

# functionsモジュールをインポートするためにパスを追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from functions import handler


class TestLambdaHandler:
    """Lambda関数の単体テスト"""

    @patch('functions.handler._get_table')
    def test_get_all_items(self, mock_get_table):
        """全アイテム取得のテスト"""
        # モックの設定
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_table.scan.return_value = {
            'Items': [
                {'id': '1', 'name': 'Item 1'},
                {'id': '2', 'name': 'Item 2'}
            ]
        }

        # イベントの作成
        event = {
            'httpMethod': 'GET',
            'path': '/items',
            'pathParameters': None,
            'body': None
        }

        # 実行
        response = handler.lambda_handler(event, None)

        # 検証
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body) == 2
        assert body[0]['id'] == '1'
        mock_table.scan.assert_called_once()

    @patch('functions.handler._get_table')
    def test_get_single_item(self, mock_get_table):
        """単一アイテム取得のテスト"""
        # モックの設定
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_table.get_item.return_value = {
            'Item': {'id': '123', 'name': 'Test Item', 'price': 1000}
        }

        # イベントの作成
        event = {
            'httpMethod': 'GET',
            'path': '/items/123',
            'pathParameters': {'id': '123'},
            'body': None
        }

        # 実行
        response = handler.lambda_handler(event, None)

        # 検証
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['id'] == '123'
        assert body['name'] == 'Test Item'
        mock_table.get_item.assert_called_once_with(Key={'id': '123'})

    @patch('functions.handler._get_table')
    def test_get_item_not_found(self, mock_get_table):
        """存在しないアイテム取得のテスト"""
        # モックの設定
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_table.get_item.return_value = {}

        # イベントの作成
        event = {
            'httpMethod': 'GET',
            'path': '/items/999',
            'pathParameters': {'id': '999'},
            'body': None
        }

        # 実行
        response = handler.lambda_handler(event, None)

        # 検証
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['message'] == 'Item not found'

    @patch('functions.handler._get_table')
    @patch('functions.handler.datetime')
    def test_create_item(self, mock_datetime, mock_get_table):
        """アイテム作成のテスト"""
        # モックの設定
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_datetime.now.return_value.timestamp.return_value = 1732176000.0
        mock_datetime.now.return_value.isoformat.return_value = '2024-11-21T10:00:00'

        # イベントの作成
        event = {
            'httpMethod': 'POST',
            'path': '/items',
            'pathParameters': None,
            'body': json.dumps({'name': 'New Item', 'price': 500})
        }

        # 実行
        response = handler.lambda_handler(event, None)

        # 検証
        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['name'] == 'New Item'
        assert body['price'] == 500
        assert 'id' in body
        assert 'createdAt' in body
        mock_table.put_item.assert_called_once()

    @patch('functions.handler._get_table')
    @patch('functions.handler.datetime')
    def test_update_item(self, mock_datetime, mock_get_table):
        """アイテム更新のテスト"""
        # モックの設定
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_datetime.now.return_value.isoformat.return_value = '2024-11-21T11:00:00'

        # イベントの作成
        event = {
            'httpMethod': 'PUT',
            'path': '/items/123',
            'pathParameters': {'id': '123'},
            'body': json.dumps({'name': 'Updated Item', 'price': 1500})
        }

        # 実行
        response = handler.lambda_handler(event, None)

        # 検証
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['id'] == '123'
        assert body['name'] == 'Updated Item'
        assert body['price'] == 1500
        assert 'updatedAt' in body
        mock_table.put_item.assert_called_once()

    @patch('functions.handler._get_table')
    def test_delete_item(self, mock_get_table):
        """アイテム削除のテスト"""
        # モックの設定
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        
        # イベントの作成
        event = {
            'httpMethod': 'DELETE',
            'path': '/items/123',
            'pathParameters': {'id': '123'},
            'body': None
        }

        # 実行
        response = handler.lambda_handler(event, None)

        # 検証
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Item deleted'
        mock_table.delete_item.assert_called_once_with(Key={'id': '123'})

    def test_create_response(self):
        """レスポンス作成関数のテスト"""
        response = handler.create_response(200, {'message': 'success'})
        
        assert response['statusCode'] == 200
        assert 'Content-Type' in response['headers']
        assert response['headers']['Content-Type'] == 'application/json'
        assert 'Access-Control-Allow-Origin' in response['headers']
        
        body = json.loads(response['body'])
        assert body['message'] == 'success'

    @patch('functions.handler.boto3')
    def test_get_table_initialization(self, mock_boto3):
        """_get_table関数の初期化テスト"""
        # グローバル変数をリセット
        handler.dynamodb = None
        handler.table = None
        
        # モックの設定
        mock_resource = MagicMock()
        mock_table = MagicMock()
        mock_boto3.resource.return_value = mock_resource
        mock_resource.Table.return_value = mock_table
        
        # 実行
        result = handler._get_table()
        
        # 検証
        assert result == mock_table
        mock_boto3.resource.assert_called_once_with('dynamodb')
        mock_resource.Table.assert_called_once_with('test-table')

    def test_decimal_encoder(self):
        """DecimalEncoderのテスト"""
        from decimal import Decimal
        encoder = handler.DecimalEncoder()
        
        # Decimal型のテスト
        result = encoder.default(Decimal('123.45'))
        assert result == 123.45
        assert isinstance(result, float)
        
        # 通常のオブジェクトのテスト（例外が発生することを確認）
        with pytest.raises(TypeError):
            encoder.default(object())

    @patch('functions.handler._get_table')
    def test_put_without_id_error(self, mock_get_table):
        """PUT要求でIDが無い場合のエラーテスト"""
        # モックの設定
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        
        # イベントの作成（pathParametersがNone）
        event = {
            'httpMethod': 'PUT',
            'path': '/items',
            'pathParameters': None,
            'body': json.dumps({'name': 'Updated Item'})
        }

        # 実行
        response = handler.lambda_handler(event, None)

        # 検証
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['message'] == 'ID is required'

    @patch('functions.handler._get_table')
    def test_delete_without_id_error(self, mock_get_table):
        """DELETE要求でIDが無い場合のエラーテスト"""
        # モックの設定
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        
        # イベントの作成（pathParametersがNone）
        event = {
            'httpMethod': 'DELETE',
            'path': '/items',
            'pathParameters': None,
            'body': None
        }

        # 実行
        response = handler.lambda_handler(event, None)

        # 検証
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['message'] == 'ID is required'

    @patch('functions.handler._get_table')
    def test_unsupported_method(self, mock_get_table):
        """サポートされていないHTTPメソッドのテスト"""
        # モックの設定
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        
        # イベントの作成
        event = {
            'httpMethod': 'PATCH',
            'path': '/items',
            'pathParameters': None,
            'body': None
        }

        # 実行
        response = handler.lambda_handler(event, None)

        # 検証
        assert response['statusCode'] == 405
        body = json.loads(response['body'])
        assert body['message'] == 'Method not allowed'

    @patch('functions.handler._get_table')
    def test_exception_handling(self, mock_get_table):
        """例外処理のテスト"""
        # モックの設定（例外を発生させる）
        mock_get_table.side_effect = Exception('Database connection error')
        
        # イベントの作成
        event = {
            'httpMethod': 'GET',
            'path': '/items',
            'pathParameters': None,
            'body': None
        }

        # 実行
        response = handler.lambda_handler(event, None)

        # 検証
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['message'] == 'Internal server error'
        assert 'error' in body
