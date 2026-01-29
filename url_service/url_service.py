# type: ignore
import asyncio
import json
import ssl
import socket
import uuid
from datetime import datetime
from urllib.parse import urlparse

import httpx
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

KAFKA_BOOTSTRAP = "data_streaming:9092"
INPUT_TOPIC = "url.to_analyze"
OUTPUT_TOPIC = "url.deep_analysis"
GROUP_ID = "url-analyzer-group" # kafka consumer group

async def get_ssl_info(hostname: str):
    try:
        ctx = ssl.create_default_context()
        reader, writer = await asyncio.open_connection(hostname, 443, ssl=ctx)
        cert = writer.get_extra_info("ssl_object").getpeercert()
        writer.close()
        await writer.wait_closed()

        issuer = dict(cert.get("issuer")[0])["commonName"]
        return True, issuer
    except:
        return False, ""


async def analyze_url(url: str):
    result = {
        "analysis_id": str(uuid.uuid4()),
        "original_url": url,
        "final_url": url,
        "redirect_chain": [],
        "http_status": None,
        "ssl_valid": False,
        "ssl_issuer": "",
        "suspicious_elements": [],
        "analysis_timestamp": datetime.utcnow().isoformat(),
    }

    parsed = urlparse(url)

    # SSL
    if parsed.scheme == "https":
        result["ssl_valid"], result["ssl_issuer"] = await get_ssl_info(parsed.hostname)

    suspicious_patterns = [
        "login", "verify", "account", "secure", "password",
        "update", "confirm", "bank", "paypal", "amazon"
    ]

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            resp = await client.head(url) # usiamo HTTP HEAD (follow redirects in maniera efficiente)
            result["http_status"] = resp.status_code
            result["final_url"] = str(resp.url)
            result["redirect_chain"] = [str(r.url) for r in resp.history]

        if any(p in url.lower() for p in suspicious_patterns):
            result["suspicious_elements"].append("suspicious_keywords")

        if len(parsed.path) > 100:
            result["suspicious_elements"].append("long_path")

        if "@" in parsed.netloc:
            result["suspicious_elements"].append("embedded_credentials")

    except Exception as e:
        result["error"] = str(e)

    return result


async def main():
    consumer = AIOKafkaConsumer(
        INPUT_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=GROUP_ID,
        value_deserializer=lambda m: json.loads(m.decode()),
    )

    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode(),
    )

    await consumer.start()
    await producer.start()

    try:
        async for msg in consumer:
            url_event = msg.value
            url = url_event["original_url"]

            analysis = await analyze_url(url)

            output_event = {
                "message_id": url_event["message_id"],
                "original_url": url,
                "analysis": analysis,
            }

            await producer.send_and_wait(OUTPUT_TOPIC, output_event)

    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
