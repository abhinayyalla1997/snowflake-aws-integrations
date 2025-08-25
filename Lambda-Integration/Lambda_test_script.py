import json
import boto3
import snowflake.connector

def lambda_handler(event, context):
    # Secret name in Secrets Manager
    secret_name = "glue-snowflake"
    region_name = "us-east-1"  # change if needed

    # Get secret from AWS Secrets Manager
    client = boto3.client("secretsmanager", region_name=region_name)
    secret_response = client.get_secret_value(SecretId=secret_name)
    secret_dict = json.loads(secret_response["SecretString"])

    # Extract Snowflake credentials
    conn = snowflake.connector.connect(
        user=secret_dict["sfUser"],
        password=secret_dict["sfPassword"],
        account=secret_dict["sfURL"].split(".")[0],  # just account locator
        warehouse=secret_dict["sfWarehouse"],
        database=secret_dict["sfDatabase"],
        schema=secret_dict["sfSchema"],
        role=secret_dict["sfRole"]
    )

    try:
        cur = conn.cursor()

        # Example: insert into USERS table
        insert_sql = "INSERT INTO USERS (NAME, AGE) VALUES (%s, %s)"
        cur.execute(insert_sql, ("aws_User", 32))  # Example row

        conn.commit()
        return {"statusCode": 200, "body": "Row inserted successfully into USERS!"}

    finally:
        cur.close()
        conn.close()
