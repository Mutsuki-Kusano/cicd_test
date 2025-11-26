import json
import os
from datetime import datetime
import boto3
from decimal import Decimal

# グローバル変数として宣言（遅延初期化）
dynamodb = None
table = None

def _get_table():
    """DynamoDBテーブルを取得（遅延初期化）"""
    global dynamodb, table
    if table is None:
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ['TABLE_NAME']
        table = dynamodb.Table(table_name)
    return table

class DecimalEncoder(json.JSONEncoder):
    """DynamoDBのDecimal型をJSONに変換するためのエンコーダー"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    try:
        table = _get_table()
        method = event['httpMethod']
        path = event['path']
        path_parameters = event.get('pathParameters') or {}
        item_id = path_parameters.get('id')

        if method == 'GET':
            if item_id:
                # 単一アイテム取得
                response = table.get_item(Key={'id': item_id})
                item = response.get('Item')
                if item:
                    return create_response(200, item)
                else:
                    return create_response(404, {'message': 'Item not found'})
            else:
                # 全アイテム取得
                response = table.scan()
                items = response.get('Items', [])
                return create_response(200, items)

        elif method == 'POST':
            # アイテム作成
            body = json.loads(event.get('body', '{}'))
            new_item = {
                'id': str(int(datetime.now().timestamp() * 1000)),
                **body,
                'createdAt': datetime.now().isoformat()
            }
            table.put_item(Item=new_item)
            return create_response(201, new_item)

        elif method == 'PUT':
            # アイテム更新
            if not item_id:
                return create_response(400, {'message': 'ID is required'})
            
            body = json.loads(event.get('body', '{}'))
            updated_item = {
                'id': item_id,
                **body,
                'updatedAt': datetime.now().isoformat()
            }
            table.put_item(Item=updated_item)
            return create_response(200, updated_item)

        elif method == 'DELETE':
            # アイテム削除
            if not item_id:
                return create_response(400, {'message': 'ID is required'})
            
            table.delete_item(Key={'id': item_id})
            return create_response(200, {'message': 'Item deleted'})

        else:
            return create_response(405, {'message': 'Method not allowed'})

    except Exception as e:
        print(f'Error: {str(e)}')
        return create_response(500, {
            'message': 'Internal server error',
            'error': str(e)
        })

def create_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(body, cls=DecimalEncoder, ensure_ascii=False)
    }
