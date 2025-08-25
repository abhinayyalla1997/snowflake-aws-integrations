# AWS Glue → Snowflake Integration (Custom Connector Approach)

***

This document explains how we integrated **AWS Glue** with **Snowflake** using a **custom Snowflake Spark connector JAR** instead of the AWS Marketplace connector.

***

## Overview

* **Goal:** Move/test data from AWS Glue into Snowflake securely.
* **Connector:** Snowflake Spark Connector JAR uploaded to S3.
* **Connection:**
* **Secrets:** Credentials managed via AWS Secrets Manager.
* **Testing:** PySpark script in Glue job writing sample data to a Snowflake table.

***

## Steps

### Step 1: Upload Snowflake Connector to S3

* Download the **Snowflake Spark Connector JAR** (and JDBC driver if needed) from Snowflake’s Maven repo.
* Upload the JAR(s) to an S3 bucket:

```javascript
s3://<your-bucket>/snowflake/spark-snowflake_2.12-<version>.jar
```

***

### Step 2: Create Custom Glue Connector

* In AWS Glue → **Connections → Create connection**.
* Choose **Custom Connector**.
* Provide:
  * **Name:** `snowflake-connector`
  * **Connector Type:** Spark
  * **S3 path:** point to the JARs uploaded in Step 1.
  * **Classname:** net.snowflake.client.jdbc.SnowflakeDriver
* Save connection.

***

## Step 3: Create Snowflake Connection in Glue

1. Go to **Glue Console → Connections → Add connection**.

2. Choose:

   * **Connector**: Snowflake Spark Connector (from Step 1)
   * **Connection type**: created custom connector

3. Provide Snowflake details:

   * **JDBC URL** → `rbmzuuc-mxc36607.snowflakecomputing.com` (no need to prefix with `jdbc:` for Spark connector)
   * **Database** → `O2BKIDS_DB`
   * **Schema** → `GLUE`
   * **Warehouse** → `DEV_WAREHOUSE`
   * **Role** → `GLUE_ROLE` (if required)

4. **Authentication** → Select Secrets Manager and link secret `glue-snowflake-up`.

5. **Save** → Test connection.

***

### Step 4: Store Snowflake Credentials in Secrets Manager

* Create a new secret in **AWS Secrets Manager** with JSON format:

```javascript
{
  "username": "SNOWFLAKE_USER",
  "password": "SNOWFLAKE_PASSWORD"
}
```

* Name it: `glue-snowflake-up`.
* Note the ARN.

***

### Step 5: Configure IAM Role for Glue

* Create an IAM role for Glue job execution.
* Attach policies:
  * `AmazonS3FullAccess` (or scoped-down access to your connector JAR/data bucket).
  * `SecretsManagerReadWrite` (or `GetSecretValue` permission for `glue-snowflake-up`).
* Update **trust policy** for `glue.amazonaws.com`.

***

### Step 6: Create Glue Job

* Create a new Glue job (Spark, Python).
* Attach:
  * **IAM Role** from Step 4.
  * **Custom Connector** (`snowflake-connector`).
* Job parameters:
  * `-extra-jars` → `s3://<bucket>/snowflake/*.jar`

***

### Step 7: Glue Job Script (Test Write to Snowflake)

```javascript
import sys
import boto3
import json
from pyspark.context import SparkContext
from awsglue.context import GlueContext

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# --- Fetch Snowflake creds from Secrets Manager ---
secret_name = "glue-snowflake-up"
region_name = "us-east-1"

session = boto3.session.Session()
client = session.client(service_name="secretsmanager", region_name=region_name)

get_secret_value_response = client.get_secret_value(SecretId=secret_name)
secret_dict = json.loads(get_secret_value_response["SecretString"])

# --- Map Snowflake options ---
sfOptions = {
    "sfURL": "RBMZUUC-MXC36607.snowflakecomputing.com",   # hardcoded
    "sfDatabase": "O2BKIDS_DB",                          # hardcoded
    "sfSchema": "GLUE",                                  # hardcoded
    "sfWarehouse": "DEV_WAREHOUSE",                      # hardcoded
    "sfRole": "GLUE_ROLE",                               # optional
    "sfUser": secret_dict["username"],                   # from secret
    "sfPassword": secret_dict["password"]                # from secret
}

# --- Example DataFrame ---
data = [("Abhi", 5), ("aob", 70), ("Calie", 385)]
columns = ["NAME", "AGE"]
df_write = spark.createDataFrame(data, columns)

# --- Write to Snowflake ---
(
    df_write.write
    .format("snowflake")
    .options(**sfOptions)
    .option("dbtable", "USERS")   # only table name (db & schema already provided)
    .mode("append")
    .save()
)
```

***

### Step 8: Run Job & Verify in Snowflake

* Run Glue job.
* Query Snowflake:

```javascript
SELECT * FROM O2BKIDS_DB.GLUE.USERS;
```

* You should see sample records inserted.

***

## ⚙️ Important Configurations

* **Connector**: Custom (Snowflake JARs uploaded to S3).
* **Secrets Manager**: `glue-snowflake-up` → username & password JSON.
* **IAM Role**: must allow S3 (for connector JARs) + Secrets Manager access.
* **sfOptions**: explicitly define Snowflake URL, Database, Schema, Warehouse.
* **Table Reference**: only table name in `.option("dbtable")` since DB & Schema provided separately.

***

✅ This completes the end-to-end setup of **Glue → Snowflake integration using a custom connector and connection in glue**.

          
