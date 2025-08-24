# snowflake-aws-integrations
This  repo includes integration of AWS cloud services with snowflake


title: 🔗 Snowflake and AWS S3 Integration Guide
created at: Fri Aug 01 2025 11:25:14 GMT+0000 (Coordinated Universal Time)
updated at: Wed Aug 20 2025 17:03:33 GMT+0000 (Coordinated Universal Time)
---

# 🔗 Snowflake and AWS S3 Integration Guide

***

This guide walks through the integration of Snowflake with AWS S3 using **Storage Integrations**. It allows Snowflake to access S3 securely via IAM role delegation.

### Step-by-Step Integration

***

### Step 1: Create Database, Schema, and Use a Warehouse

Before connecting to S3, you must have a **database** and **schema** in Snowflake to define objects like stages. You can use the **default warehouse** or create a new one if needed.

```javascript
-- Create a database and schema
CREATE DATABASE IF NOT EXISTS my_s3_data_db;
CREATE SCHEMA IF NOT EXISTS my_s3_data_db.external_data;

-- Select them for current session
USE DATABASE my_s3_data_db;
USE SCHEMA external_data;

-- (Optional) Use default or create new warehouse
USE WAREHOUSE compute_wh;
```

***

### Step 2: Create IAM Policy in AWS

Create a custom IAM policy in AWS with permissions to access the S3 bucket and prefix:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:DeleteObject",
        "s3:DeleteObjectVersion"
      ],
      "Resource": "arn:aws:s3:::<bucket>/<prefix>/*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket", "s3:GetBucketLocation"],
      "Resource": "arn:aws:s3:::<bucket>",
      "Condition": {
        "StringLike": {
          "s3:prefix": ["<prefix>/*"]
        }
      }
    }
  ]
}
```

Replace `<bucket>` and `<prefix>` with your actual values.

***

### Step 3: Create IAM Role

Create a role in AWS IAM:

* **Trusted entity:** Another AWS account (Snowflake’s AWS account)
* **AWS Account ID:** Placeholder for now
* **External ID:** Placeholder for now

Attach the policy from Step 2 to this role.

You will update this later with actual values obtained from Snowflake in Step 5.

***

### Step 4: Create Storage Integration in Snowflake

```javascript
CREATE STORAGE INTEGRATION s3_int
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::<your-aws-account>:role/<your-role>'
  STORAGE_ALLOWED_LOCATIONS = ('s3://your-bucket/prefix/');
```

Replace the role ARN with the one created in Step 3.

***

### Step 5: Describe Integration

Use this to retrieve AWS Account ID and External ID provided by Snowflake:

```javascript
DESC INTEGRATION s3_int;
```

You will see fields like:

* **STORAGE\_AWS\_IAM\_USER\_ARN**
* **STORAGE\_AWS\_EXTERNAL\_ID**

Use these to update the **trust policy** in the IAM role from Step 3.

***

### Step 6: Grant Privileges

```javascript
-- Grant necessary permissions
GRANT USAGE ON INTEGRATION s3_int TO ROLE myrole;
GRANT CREATE STAGE ON SCHEMA external_data TO ROLE myrole;
```

These permissions allow the role to use the integration and create a stage.

***

> ⚠️ **Note on Roles and Permissions:**\
> If you are using a role other than `ACCOUNTADMIN` (e.g., `SYSADMIN`), ensure that the role has the necessary privileges. The `SYSADMIN` role can grant `CREATE STAGE` on schemas it owns. However, only the role that created the storage integration — typically `ACCOUNTADMIN` — can grant `USAGE` on that integration. Therefore, if `SYSADMIN` did not create the integration, an `ACCOUNTADMIN` must run:

```javascript
GRANT USAGE ON INTEGRATION s3_int TO ROLE SYSADMIN;
GRANT CREATE STAGE ON SCHEMA external_data TO ROLE SYSADMIN;
```

> Once this is granted, `SYSADMIN` can proceed to create the external stage and perform data operations within its authorized schemas.

***

### Step 7: Create the External Stage

```javascript
CREATE STAGE my_s3_stage
  STORAGE_INTEGRATION = s3_int
  URL = 's3://your-bucket/prefix/';
```

This creates a named stage in Snowflake pointing to your S3 path, enabling data access.

***

### Step 8: List Data in Stage

```javascript
LIST @my_s3_stage;
```

This command verifies that Snowflake can access the S3 bucket using the integration.

***

## 📝 Summary (Important Notes)

* In **Step 1**, creating a **database and schema** is required because all Snowflake objects (like stages) live inside a schema.
* In **Step 4**, `STORAGE_AWS_ROLE_ARN` is the role you created in AWS.
* In **Step 5**, the `DESC INTEGRATION` command provides the **AWS Account ID** and **External ID** you must paste into the **trust policy** of the IAM role. This step ensures **Snowflake can securely assume your AWS role**.
* In **Step 6**, permissions are mandatory to let your Snowflake role use the storage integration and create a stage.
* In **Step 7**, `CREATE STAGE` ties everything together — it defines where Snowflake looks in S3, using the integration securely.

***

### 📚 References

* 📄 [Official Snowflake Documentation](https://docs.snowflake.com/en/user-guide/data-load-s3-config-storage-integration)

***

[Reading a Text File from S3 in Snowflake (Support.txt)](https://slite.com/api/public/notes/OVAIuy2lzPSoPz/redirect)

          
