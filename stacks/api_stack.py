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
    def __init__(self, scope: Construct, construct_id: str, environment: str = 'dev', **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 環境別のリソース名プレフィックス
        env_prefix = f"{environment}-"

        # DynamoDBテーブル作成
        table = dynamodb.Table(
            self, f"{env_prefix}ItemsTable",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY if environment != 'prod' else RemovalPolicy.RETAIN,
            table_name=f"{env_prefix}items-table"
        )

        # Lambda関数作成
        handler = _lambda.Function(
            self, f"{env_prefix}ApiHandler",
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset("functions"),
            handler="handler.lambda_handler",
            function_name=f"{env_prefix}api-handler",
            environment={
                "TABLE_NAME": table.table_name,
                "ENVIRONMENT": environment,
            },
        )

        # LambdaにDynamoDBへのアクセス権限を付与
        table.grant_read_write_data(handler)

        # API Gateway作成
        api = apigateway.RestApi(
            self, f"{env_prefix}ItemsApi",
            rest_api_name=f"{env_prefix}Items Service",
            description=f"API for managing items ({environment} environment)",
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
            self, f"{env_prefix}ApiUrl",
            value=api.url,
            description=f"API Gateway URL ({environment})",
            export_name=f"{construct_id}-ApiUrl"
        )

        CfnOutput(
            self, f"{env_prefix}TableName",
            value=table.table_name,
            description=f"DynamoDB Table Name ({environment})",
            export_name=f"{construct_id}-TableName"
        )
