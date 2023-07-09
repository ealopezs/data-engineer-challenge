import asyncio
from streamproducer import StreamProducer

if __name__ == "__main__":
    producer = StreamProducer()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(producer.start())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()