
import logging
import paho.mqtt.client as mqtt
import boto3
import json
import datetime
from settings import get_settings

class Processor:
    def __init__(self):
        self.settings = get_settings()
        self.mqtt_client = mqtt.Client()

        if self.settings.mqtt.username:
            self.mqtt_client.username_pw_set(
                self.settings.mqtt.username, self.settings.mqtt.password
            )
            
        with open('credentials.json', 'r') as f:
            config = json.load(f)
            aws_conf_access_key_id=config["aws"]["access_key_id"]
            aws_conf_secret_access_key=config["aws"]["secret_access_key"]
            aws_conf_session_token=config["aws"]["session_token"]
            aws_region=config["aws"]["region"]
            
        session = boto3.session.Session(
        region_name=aws_region,
        aws_access_key_id= aws_conf_access_key_id,
        aws_secret_access_key= aws_conf_secret_access_key,   
        aws_session_token = aws_conf_session_token
        )
        self.s3_client  = session.client('s3')
        
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
    def start(self):
        logging.basicConfig(level=self.settings.logging_level)
        self.mqtt_client.connect(self.settings.mqtt.host, self.settings.mqtt.port)
        self.mqtt_client.loop_forever()

    def on_connect(self, client, userdata, flags, rc):
        logging.info("Connected to MQTT broker")
        client.subscribe(self.settings.mqtt.topic)

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        logging.info(f"Received message: {payload}")
        
        #Store the IoT data in raw format to S3 bucket
        self.store_raw_data(payload)

    def store_raw_data(self, data):
        bucket_name = "iotrawinput"
        folder_name = datetime.datetime.now().strftime("%Y-%m-%d")
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
         # Extract the sensor id
        sensor_id = json.loads(data).get("id")

        object_key = f"raw_data/{folder_name}/{self.settings.mqtt.topic}/{sensor_id}/{current_datetime}.json"
        
        try:
            self.s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=data)
            logging.info(f"Stored data to S3 bucket: {bucket_name}/{object_key}")
        except Exception as e:
            logging.error(f"Error storing data to S3: {e}")
