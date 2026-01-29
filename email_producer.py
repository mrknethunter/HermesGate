import sys
import json
import socket
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, date_format

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mail_producer")

argv = sys.argv

if len(sys.argv) != 3:
    print("Bad arguments")
    print(f"Usage: python3 {argv[0]} <csv_file> <num_record>")
    sys.exit(1)

csv_path = argv[1]
num_records_requested = int(argv[2])

LOGSTASH_HOST = "localhost"
LOGSTASH_PORT = 5000


spark = SparkSession \
    .builder \
    .appName("mail_producer") \
    .getOrCreate()

# spark.sparkContext.setLogLevel("ERROR")

logger.info(f"Reading CSV {csv_path}")

df = spark.read.csv(
    csv_path,
    header=True,
    sep=",",
    quote='"',
    escape='"',
    multiLine=True
)

total_records = df.count()
logger.info(f"Records = {total_records}")

if num_records_requested > total_records:
    logger.error(f"{num_records_requested} record requested, but only {total_records} in CSV file\nExiting...")

    spark.stop()
    sys.exit(1)

emails_df = df.select(
    col("sender"),
    col("receiver"),
    date_format(
        to_timestamp(col("date")),
        "yyyy-MM-dd'T'HH:mm:ss'Z'"
    ).alias("date"),
    col("subject"),
    col("body")
).limit(num_records_requested)

logger.info("finish dataframe parsing")

rows = emails_df.collect()

try:
    logger.info(f"Apertura connessione TCP a {LOGSTASH_HOST}:{LOGSTASH_PORT}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((LOGSTASH_HOST, LOGSTASH_PORT))
    count = 0
    for row in rows:
        json_msg = {
            "sender": row["sender"],
            "receiver": row["receiver"],
            "date": row["date"],
            "subject": row["subject"],
            "body": row["body"]
        }

        msg_str = json.dumps(json_msg)
        sock.sendall((msg_str + "\n").encode("utf-8"))
        count += 1

        if count % 100 == 0:
            logger.info(f"Sent {count} records so far")

    logger.info(f"Sent {count} records, closing TCP connection")
    sock.close()
except Exception as e:
    logger.exception(f"Error during records sending: {e}")


