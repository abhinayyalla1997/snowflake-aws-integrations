# Lambda Integration with Snowflake

This document outlines the complete steps and configuration for integrating an AWS Lambda function with **Snowflake** using **AWS Secrets Manager**, **VPC Endpoints**, and **NAT Gateway**.

***

## 1. Architecture Overview

* Lambda function runs inside a **private subnet** within a VPC.
* Secrets (Snowflake credentials) are securely stored in **AWS Secrets Manager**.
* Lambda retrieves secrets through a **VPC Interface Endpoint** for `secretsmanager`.
* Lambda accesses Snowflake (which is an external SaaS service over the internet) via a **NAT Gateway** placed in a public subnet.
* A **Lambda Layer** is used to package the `snowflake-connector-python` library.

**Flow:**

```javascript
Lambda (Private Subnet)
   → Secrets Manager (via VPC Endpoint)
   → NAT Gateway (via route table)
   → Internet → Snowflake
```

***

## 2. Key Steps Performed

### a. VPC Endpoint (Secrets Manager)

* Created an **interface endpoint** for `com.amazonaws.us-east-1.secretsmanager`.
* Associated it with the **private subnets** where Lambda runs.
* Security Group rules:
  * **Lambda SG outbound** → allow all traffic.
  * **Endpoint SG inbound** → allow traffic from Lambda SG.

### b. NAT Gateway Setup

* Created an **Elastic IP**.
* Created a **NAT Gateway** in one of the public subnets.
* Attached the Elastic IP to the NAT Gateway.
* Updated **route tables** for private subnets:
  * Route `0.0.0.0/0` → NAT Gateway.

This ensures Lambda in private subnet can connect to external Snowflake endpoints.

### c. Security Groups

* **Lambda Security Group**:
  * Outbound: `0.0.0.0/0` (all traffic allowed).
* **Secrets Manager Endpoint SG**:
  * Inbound: Allow traffic from Lambda SG.

### d. Lambda Layer

* Created a **Lambda Layer** containing `snowflake-connector-python` library.

[\[snowflake\_layer.zip (27MB)\]](media_Lambda%20Integration%20with%20Snowflake/dcQ1_fzFRdAV_d-snowflake_layer.zip)

* Attached the layer to the Lambda function to enable Snowflake connectivity.

***

## 3. Lambda Test Script

We used the following Python Lambda function to test integration with Snowflake:

```javascript
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
```

***

## 4. Outcome

After applying the above steps:

* Lambda successfully retrieved secrets from **Secrets Manager**.
* Lambda connected to **Snowflake** via NAT Gateway.
* Test query (`INSERT INTO USERS`) executed successfully.

✅ Integration completed and verified.

          
