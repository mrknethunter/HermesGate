# config file

# spark internals
SPARK_APP_NAME = "HermesSparkProcessing"
URL_EXTRACTOR_NAME = "Hermes_URL_Extractor"
MODEL_PATH = "/code/spark_processing/spark_pipeline_v2/"

# kafka
KAFKA_BOOTSTRAP = "kafka:9092"
TOPIC_EMAIL_RAW = "email.raw"
TOPIC_EMAIL_PARSED = "email.parsed"
TOPIC_PREDICTIONS = "email.predictions"
TOPIC_URL_TO_ANALYZE = "url.to_analyze"

# checkpoint
CHK_STREAM = "/tmp/checkpoints/stream"
CHK_METRICS = "/tmp/checkpoints/metrics"

# TF IDF
NUM_TFIDF_FEATURES = 300
