# config.py

SPARK_APP_NAME_TRAIN = "PhishingTraining"
SPARK_APP_NAME_STREAM = "PhishingStreaming"

MODEL_PATH = "/mnt/c/Users/manga/Downloads/test_email_detector/spark_pipeline_v2"

# Kafka
KAFKA_BOOTSTRAP = "localhost:9092"
TOPIC_EMAILS = "emails"
TOPIC_PREDICTIONS = "predictions"
TOPIC_METRICS = "metrics"

# Checkpoints
CHK_STREAM = "/tmp/checkpoints/stream"
CHK_METRICS = "/tmp/checkpoints/metrics"

# TF-IDF
NUM_TFIDF_FEATURES = 300
