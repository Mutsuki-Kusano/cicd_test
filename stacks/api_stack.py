from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    RemovalPolicy,
    CfnOutput,
)
from constructs import Construct

class ApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDBテーブル作成
        table = dynamodb.Table(
            self, "ItemsTable",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,  # 開発用：本番環境ではRETAINを推奨
        )

        # Lambda関数作成
        handler = _lambda.Function(
            self, "ApiHandler",
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset("functions"),
            handler="handler.lambda_handler",
            environment={
                "TABLE_NAME": table.table_name,
            },
        )

        # LambdaにDynamoDBへのアクセス権限を付与
        table.grant_read_write_data(handler)

        # API Gateway作成
        api = apigateway.RestApi(
            self, "ItemsApi",
            rest_api_name="Items Service",
            description="API for managing items",
        )

        items = api.root.add_resource("items")
        items.add_method("GET", apigateway.LambdaIntegration(handler))
        items.add_method("POST", apigateway.LambdaIntegration(handler))

        item = items.add_resource("{id}")
        item.add_method("GET", apigateway.LambdaIntegration(handler))
        item.add_method("PUT", apigateway.LambdaIntegration(handler))
        item.add_method("DELETE", apigateway.LambdaIntegration(handler))

        # 出力
        CfnOutput(
            self, "ApiUrl",
            value=api.url,
            description="API Gateway URL",
        )

        CfnOutput(
            self, "TableName",
            value=table.table_name,
            description="DynamoDB Table Name",
        )
