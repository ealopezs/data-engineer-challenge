import logging
import asyncio
import json
from kafka import KafkaProducer
from kafka.errors import KafkaError
from settings import get_settings
import paho.mqtt.client as mqtt

# This class "stream producer" service will consume the MQTT messages and publish them to a Kafka topic.
# Added appropriate error handling and logging for failures during producer initialization and message processing.
# Also, error handling and logging have been added to manage stability and handle asynchronous function failures. 

class StreamProducer:
    def __init__(self):
        #Kafka config were added to settings
        self.settings = get_settings()
        # Kafka producer variable
        self.producer = None
        #Set MQTT cliet
        self.mqtt_client = mqtt.Client()

    async def start(self):
        logging.basicConfig(level=self.settings.logging_level)

        try:
            #Initialization of the KafkaProducer
            self.initialize_producer()
            await self.receive_messages()
        except Exception as e:
            logging.exception(f"An error occurred: {str(e)}")

    # This method set the kafka server to handle the initialization of the KafkaProducer with a retry logic.
    def initialize_producer(self):
        while True:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.settings.kafka.bootstrap_servers
                )
                break
            except KafkaError as e:
                logging.error(f"Failed to initialize KafkaProducer: {str(e)}")
                asyncio.sleep(10)  # Retry after 10 seconds

    # The receive_messages method is an asynchronous loop that retrieves messages and publishes them to the Kafka topic using the producer.
    async def receive_messages(self):
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect(self.settings.mqtt.host, self.settings.mqtt.port)
        self.mqtt_client.subscribe(self.settings.mqtt.topic)
        self.mqtt_client.loop_start()
        
    def on_message(self, client, userdata, msg):
        message = msg.payload.decode('utf-8')
        parsed_message = json.loads(message)
        logging.error(f"Message received: {str(parsed_message)}")
        self.publish_message(parsed_message)

    # Publish the message to the Kafka topic
    def publish_message(self, message):
        try:
            json_message = json.dumps(message)
            self.producer.send(self.settings.kafka.topic, value=json_message.encode('utf-8'))
            self.producer.flush()
        except Exception as e:
                logging.exception(f"An error occurred during message processing: {str(e)}")