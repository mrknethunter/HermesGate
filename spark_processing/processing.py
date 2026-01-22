# type: ignore
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline, PipelineModel
from pyspark.ml.classification import GBTClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from config import *
from pyspark.sql.functions import size, split, col, when, coalesce, array, from_json, length, regexp_replace, regexp_extract_all, lit, struct, to_json
import time
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType

spark = SparkSession.builder. \
    appName(SPARK_APP_NAME) \
    .getOrCreate()

# schema per feature engineering
email_raw_schema = StructType([
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

df.printSchema()
print(f"columns = {df.columns}")

# feature engineering

df = df.withColumn("label", col("label").cast("double"))

df = df \
    .withColumn("sender_digits", length(regexp_replace(col("sender"), "[^0-9]", ""))) \
    .withColumn("subj_len", length(col("subject"))) \
    .withColumn("subj_spec", length(regexp_replace(col("subject"), "[a-zA-Z0-9 ]", ""))) \
    .withColumn("body_ip", col("body").rlike(r"\b\d{1,3}(\.\d{1,3}){3}\b").cast("int")) # eventualmente limitare la len del body

# subj_spec = subj_specialchars

df = df \
    .withColumn("url_list", coalesce(
        regexp_extract_all(col("body"), lit(r"https?://[^\s<>'\"]+"), 0),
        array()
    ))

df = df \
    .withColumn("url_count", size(col("url_list")))

# per caricare modello trainato da file
model = PipelineModel.load(MODEL_PATH)

# inferenza
predictions = model.transform(df)

df.writeStream \
    .outputMode("append") \
    .queryName("dataframe") \
    .format("console") \
    .option("truncate", "false") \
    .start()

predictions.writeStream \
    .outputMode("append") \
    .queryName("predictions") \
    .format("console") \
    .option("truncate", "false") \
    .start()

predictions \
    .selectExpr(
        "CAST(null as STRING) AS key",
        "to_json(struct(*)) AS value"
    ) \
    .writeStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("topic", "email.predictions") \
    .option("checkpointLocation", CHK_STREAM) \
    .start()


spark.streams.awaitAnyTermination()

