import sys
import boto3
import json
from pyspark.context import SparkContext
from awsglue.context import GlueContext

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# --- Fetch Snowflake creds from Secrets Manager ---
secret_name = "glue-snowflake"
region_name = "us-east-1"

session = boto3.session.Session()
client = session.client(service_name="secretsmanager", region_name=region_name)

get_secret_value_response = client.get_secret_value(SecretId=secret_name)
secret_dict = json.loads(get_secret_value_response["SecretString"])

# --- Map secret values to Snowflake options ---
sfOptions = {
    "sfURL": secret_dict["sfURL"],
    "sfDatabase": secret_dict["sfDatabase"],
    "sfSchema": secret_dict["sfSchema"],
    "sfWarehouse": secret_dict["sfWarehouse"],
    "sfRole": secret_dict["sfRole"],
    "sfUser": secret_dict["sfUser"],
    "sfPassword": secret_dict["sfPassword"]
}

# --- Create example DataFrame (sample data) ---
data = [("Ale", 5), ("ob", 70), ("Chalie", 385)]
columns = ["NAME", "AGE"]

df_write = spark.createDataFrame(data, columns)

# --- Write DataFrame to Snowflake table ---
(
    df_write.write
    .format("snowflake")
    .options(**sfOptions)
    .option("dbtable", "O2BKIDS_DB.GLUE.USERS")  # fully qualified
    .mode("append")
    .save()
)