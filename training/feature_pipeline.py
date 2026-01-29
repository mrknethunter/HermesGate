# feature_pipeline.py
# type: ignore
from pyspark.sql.functions import col, length, regexp_replace
from pyspark.ml.feature import (
    Tokenizer,
    StopWordsRemover,
    HashingTF,
    IDF,
    VectorAssembler
)

def add_structural_features(df):
    return (
        df
        .withColumn("sender_digits", length(regexp_replace(col("sender"), "[^0-9]", "")))
        .withColumn("subj_len", length(col("subject")))
        .withColumn("subj_spec", length(regexp_replace(col("subject"), "[a-zA-Z0-9 ]", "")))
        .withColumn("body_ip", col("body").rlike(r"\b\d{1,3}(\.\d{1,3}){3}\b").cast("int"))
    )

def tfidf_stages(input_col, output_col, num_features):
    return [
        Tokenizer(inputCol=input_col, outputCol=f"{input_col}_tokens"),
        StopWordsRemover(
            inputCol=f"{input_col}_tokens",
            outputCol=f"{input_col}_clean"
        ),
        HashingTF(
            inputCol=f"{input_col}_clean",
            outputCol=f"{input_col}_tf",
            numFeatures=num_features
        ),
        IDF(
            inputCol=f"{input_col}_tf",
            outputCol=output_col
        )
    ]

def assembler_stage():
    return VectorAssembler(
        inputCols=[
            "sender_digits",
            "subj_len",
            "subj_spec",
            "body_ip",
            "url_count",
            "subject_tfidf",
            "body_tfidf"
        ],
        outputCol="features"
    )
