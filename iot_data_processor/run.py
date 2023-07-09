import asyncio
from processor import Processor

if __name__ == "__main__":
    processor = Processor()
    loop = asyncio.new_event_loop()
    loop.run_until_complete(processor.start())