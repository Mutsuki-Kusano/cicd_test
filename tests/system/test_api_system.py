import pytest
import requests
import json
import os
from unittest.mock import patch, MagicMock

class TestAPISystemTests:
    """
    システムテスト: エンドツーエンドのAPIテスト
    実際のAPIエンドポイントに対するテスト（モック環境）
    """
    
    @pytest.fixture
    def api_base_url(self):
        """テスト用のAPIベースURL"""
        return os.getenv('API_BASE_URL', 'https://mock-api.example.com')
    
    @pytest.fixture
    def mock_requests(self):
        """requestsライブラリをモック化"""
        with patch('requests.get') as mock_get, \
             patch('requests.post') as mock_post, \
             patch('requests.put') as mock_put, \
             patch('requests.delete') as mock_delete:
            
            # モックレスポンスの設定
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "123", "name": "test item"}
            
            mock_get.return_value = mock_response
            mock_post.return_value = mock_response
            mock_put.return_value = mock_response
            mock_delete.return_value = mock_response
            
            yield {
                'get': mock_get,
                'post': mock_post,
                'put': mock_put,
                'delete': mock_delete
            }

    def test_api_health_check(self, api_base_url, mock_requests):
        """APIヘルスチェックのシステムテスト"""
        # ヘルスチェックエンドポイントの呼び出し
        response = requests.get(f"{api_base_url}/health")
        
        # レスポンスの検証
        assert response.status_code == 200
        mock_requests['get'].assert_called_once_with(f"{api_base_url}/health")

    def test_create_item_system_flow(self, api_base_url, mock_requests):
        """アイテム作成のシステムフローテスト"""
        # テストデータ
        test_item = {
            "name": "システムテスト商品",
            "description": "システムテスト用の商品です",
            "price": 1500
        }
        
        # アイテム作成API呼び出し
        response = requests.post(
            f"{api_base_url}/items",
            json=test_item,
            headers={"Content-Type": "application/json"}
        )
        
        # レスポンスの検証
        assert response.status_code == 200
        mock_requests['post'].assert_called_once()
        
        # 呼び出し引数の検証
        call_args = mock_requests['post'].call_args
        assert call_args[0][0] == f"{api_base_url}/items"
        assert call_args[1]['json'] == test_item

    def test_get_items_system_flow(self, api_base_url, mock_requests):
        """アイテム一覧取得のシステムフローテスト"""
        # アイテム一覧取得API呼び出し
        response = requests.get(f"{api_base_url}/items")
        
        # レスポンスの検証
        assert response.status_code == 200
        mock_requests['get'].assert_called_once_with(f"{api_base_url}/items")

    def test_update_item_system_flow(self, api_base_url, mock_requests):
        """アイテム更新のシステムフローテスト"""
        item_id = "123"
        update_data = {
            "name": "更新されたシステムテスト商品",
            "price": 2000
        }
        
        # アイテム更新API呼び出し
        response = requests.put(
            f"{api_base_url}/items/{item_id}",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        
        # レスポンスの検証
        assert response.status_code == 200
        mock_requests['put'].assert_called_once()

    def test_delete_item_system_flow(self, api_base_url, mock_requests):
        """アイテム削除のシステムフローテスト"""
        item_id = "123"
        
        # アイテム削除API呼び出し
        response = requests.delete(f"{api_base_url}/items/{item_id}")
        
        # レスポンスの検証
        assert response.status_code == 200
        mock_requests['delete'].assert_called_once_with(f"{api_base_url}/items/{item_id}")

    def test_error_handling_system(self, api_base_url, mock_requests):
        """エラーハンドリングのシステムテスト"""
        # 404エラーのモック設定
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "Item not found"}
        mock_requests['get'].return_value = mock_response
        
        # 存在しないアイテムの取得
        response = requests.get(f"{api_base_url}/items/nonexistent")
        
        # エラーレスポンスの検証
        assert response.status_code == 404
        assert response.json()["message"] == "Item not found"

    def test_api_performance_basic(self, api_base_url, mock_requests):
        """基本的なパフォーマンステスト"""
        import time
        
        # レスポンス時間の測定
        start_time = time.time()
        response = requests.get(f"{api_base_url}/items")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # レスポンス時間の検証（モック環境なので非常に高速）
        assert response_time < 1.0  # 1秒以内
        assert response.status_code == 200