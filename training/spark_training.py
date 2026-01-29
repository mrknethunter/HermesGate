# type: ignore
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline, PipelineModel
from pyspark.ml.classification import GBTClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from feature_pipeline import *
from config_test import *
from pyspark.sql.functions import size, split, col, when
import time


start = time.time()

spark = SparkSession.builder.appName(SPARK_APP_NAME_TRAIN).getOrCreate()

df = spark.read.csv(
    "CEAS_08.csv",
    header=True,
    sep=",",
    quote='"',
    escape='"',
    multiLine=True
)

df = df.fillna({"sender": "unknown",
                "subject": "",
                "body": "",
                "urls": 0}) # false

df.printSchema()
print(f"columns = {df.columns}")
df.select("label").show(5, truncate=False)

df = df.withColumn("label", col("label").cast("double"))

# feature engineering

df = df \
    .withColumn("sender_digits", length(regexp_replace(col("sender"), "[^0-9]", ""))) \
    .withColumn("subj_len", length(col("subject"))) \
    .withColumn("subj_spec", length(regexp_replace(col("subject"), "[a-zA-Z0-9 ]", ""))) \
    .withColumn("body_ip", col("body").rlike(r"\b\d{1,3}(\.\d{1,3}){3}\b").cast("int")) # eventualmente limitare la len del body

# subj_spec = subj_specialchars


# Pipeline
stages = []
stages += tfidf_stages("subject", "subject_tfidf", NUM_TFIDF_FEATURES)
stages += tfidf_stages("body", "body_tfidf", NUM_TFIDF_FEATURES)
stages.append(assembler_stage())

clf = GBTClassifier(
    labelCol="label",
    featuresCol="features",
    maxIter=100,
    maxDepth=5,
    stepSize=0.1
)
stages.append(clf)

pipeline = Pipeline(stages=stages)

# dataset split
train_df, test_df = df.randomSplit([0.8, 0.2], seed=42)

model = pipeline.fit(train_df)

# per caricare modello trainato da file
# model = PipelineModel.load(MODEL_PATH)

# model evaluation
predictions = model.transform(test_df)

evaluator = BinaryClassificationEvaluator(labelCol="label")
auc = evaluator.evaluate(predictions)

accuracy = predictions.filter("prediction == label").count() / predictions.count()

print(f"AUC: {auc:.4f}")
print(f"Accuracy: {accuracy:.4f}")

end = time.time()

print(f"computing completato in {end - start:.2f} secondi")

# Save model to disk
model.write().overwrite().save(MODEL_PATH)
print(f"Model saved at {MODEL_PATH}")
