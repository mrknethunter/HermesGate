<img src="hermesgate_logo.png" alt="drawing" width="350"/>

# HermesGate - Real Time email processing pipeline for Email Security

This project is a **real-time data engineering pipeline for email security**.
It ingests email-related events, processes them in streaming, enriches them, classifies them with machine learning and makes the results searchable and observable in real time.

The goal is to create a modern **email threat detection and analysis platform**, where incoming signals are continuously processed to identify suspicious patterns, classify threats, and provide visibility through dashboards and metadata tracking.

# What HermesGate does

At a high level:

* Collects email security events
* Streams them through a distributed messaging system
* Processes and enriches data in real time
* Applies ML models for scoring / classification
* Stores results in a search engine for investigation
* Exposes multiple UIs for monitoring and exploration

Everything runs in Docker and orchestrated through **Docker Compose**, so the full stack can be reproduced easily.

# Repository clome

```bash
git clone https://github.com/mrknethunter/HermesGate.git
cd HermesGate
```

---

# Run the project

### Requirements

* Docker (with Compose)
* At least 16 GB RAM suggested for smooth operations

### Start the stack

```bash
docker compose -f <compose_file> up
```

After startup, all services will be available through local ports (see table below).

# Logical Flow

1. **Email Producers** send email security events
2. Events are ingested and normalized by **Logstash**
3. Data is streamed through **Kafka (KRaft mode)**
4. **Spark Structured Streaming** processes events in real time
5. **Spark ML** applies ML models
6. Optional semantic enrichment via **Google LLM API**
7. Processed data is indexed in **Elasticsearch**
8. Analysts explore data through **Kibana**
9. Datasets, Kafka topics, PII and Data Governance Plan are tracked in **DataHub**

# Technologies

| Technology                     | What does Here                                              |
| ------------------------------ | --------------------------------------------------------------- |
| **Docker**                     | Runs the entire platform in isolated, reproducible containers   |
| **Logstash**                   | First ingestion layer for normalizing and forwarding events         |
| **Kafka (KRaft)**              | Backbone of the streaming architecture                          |
| **Spark Structured Streaming** | Real-time data processing engine                                |
| **Spark ML**                   | ML models for detection, scoring, or classification             |
| **httpx (Python)**             | Async HTTP client             |
| **Elasticsearch**              | Stores processed events for fast search and investigation       |
| **Kibana**                     | Dashboards and exploratory analysis                             |
| **DataHub**                    | Metadata management         |
| **Google LLM API**             | Sysadmin Assistant |

---

# UI and search API exposure

| Service               | URL                                            |
| --------------------- | ---------------------------------------------- |
| **Kafka UI**          | http://localhost:8081 |
| **Kibana**            | http://localhost:5601 |
| **Elasticsearch API** | http://localhost:9200 |




# Benchmarking

For benchmarking purpose, the script email_producer.py can be used:

```bash
python3 email_producer.py <data.csv> <number_of_email>
```

For example:

```bash
python3 email_producer.py training/CEAS_08.csv 2000
```

This will generate sample (but real world) email security events and push them into the pipeline  


