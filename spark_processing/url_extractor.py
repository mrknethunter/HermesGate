# type: ignore
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import json
import uuid
from datetime import datetime
from config import *


spark = SparkSession.builder. \
    appName(URL_EXTRACTOR_NAME) \
    .master("local[*]") \
    .getOrCreate()

# schema per feature engineering
email_raw_schema = StructType([
    StructField("message_id", StringType()),
    StructField("sender", StringType()),
    StructField("receiver", StringType()),
    StructField("date", TimestampType()),
    StructField("subject", StringType()),
    StructField("body", StringType()),
    StructField("urls", StringType()),
    StructField("label", StringType()),
])

df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
    .option("subscribe", TOPIC_EMAIL_RAW) \
    .option("startingOffsets", "latest") \
    .load()

# leggiamo bytestream da kafka, qui castiamo
df = df.select(from_json(col("value").cast("string"), email_raw_schema).alias("data")) \
    .select("data.*")

# gestiamo valori mancanti
df = df.fillna({"sender": "unknown",
                "subject": "",
                "body": "",
                "urls": 0}) # false


df = df.withColumn("label", col("label").cast("double"))

df = df \
    .withColumn("url_list", coalesce(
        regexp_extract_all(col("body"), lit(r"https?://[^\s<>'\"]+"), 0),
        array()
    ))

df = df \
    .withColumn("url_count", size(col("url_list")))

# record atomici per streaming kafka (per scalabilità)
links_df = df \
    .select(
        col("message_id"),
        col("date").alias("email_timestamp"),
        explode(col("url_list")).alias("original_url")
    ) 

links_df \
    .selectExpr(
        "CAST(null as STRING) AS key",
        "to_json(struct(*)) AS value"
    ) \
    .writeStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("topic", TOPIC_URL_TO_ANALYZE) \
    .option("checkpointLocation", CHK_STREAM) \
    .start()


spark.streams.awaitAnyTermination()
