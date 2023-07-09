
import logging
import paho.mqtt.client as mqtt
import boto3
import json
import datetime
from settings import get_settings

# The Processor class handle MQTT message processing. It initializes the MQTT client and sets up the callbacks for connection and message handling.
# Also, this service takes the IoT data as input, and upload it data to a specified S3 bucket.
# The boto3 library is imported to interact with AWS S3.
# This service depends on iot data generator service and MQTT broker running properly.

class Processor:
    def __init__(self):
        self.settings = get_settings()
        #Set MQTT cliet
        self.mqtt_client = mqtt.Client()

        if self.settings.mqtt.username:
            self.mqtt_client.username_pw_set(
                self.settings.mqtt.username, self.settings.mqtt.password
            )
            
        # Set credentials from an external file to better protection
        with open('credentials.json', 'r') as f:
            config = json.load(f)
            aws_conf_access_key_id=config["aws"]["access_key_id"]
            aws_conf_secret_access_key=config["aws"]["secret_access_key"]
            aws_conf_session_token=config["aws"]["session_token"]
            aws_region=config["aws"]["region"]
            
        # Set client of AWS S3 to open connection and be able to store raw data.
        # For this approach has been necessary to use an AWS laboratory that must be activated on demand and these credentials change for each session of the Lab.
        # This service will fail at this point without updated credentials. An error similar to "Access Denied" or "Credentials have expired" will be displayed.
        # During the interview I will try to have the Lab active to show how it works.
        session = boto3.session.Session(
        region_name=aws_region,
        aws_access_key_id= aws_conf_access_key_id,
        aws_secret_access_key= aws_conf_secret_access_key,   
        aws_session_token = aws_conf_session_token
        )
        self.s3_client  = session.client('s3')
        
        # Delegate methods to process messagges from MQTT broker
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

    # Formating and store in a Bueckt S3 called "iotrawdata"
    def store_raw_data(self, data):
        bucket_name = "iotrawinput"
        folder_name = datetime.datetime.now().strftime("%Y-%m-%d")
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
         # Extract the sensor id
        sensor_id = json.loads(data).get("id")

        # It takes the IoT data payload and constructs the S3 object key.
        object_key = f"raw_data/{folder_name}/{self.settings.mqtt.topic}/{sensor_id}/{current_datetime}.json"
        
        try:
            self.s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=data)
            logging.info(f"Stored data to S3 bucket: {bucket_name}/{object_key}")
        except Exception as e:
            logging.error(f"Error storing data to S3: {e}")
