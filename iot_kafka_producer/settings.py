from typing import Optional
from pydantic import BaseSettings
from functools import lru_cache

class MqttSettings(BaseSettings):
    class Config:
        env_file = '.env'
        env_prefix = 'mqtt_'

    host: str = "mqtt_broker"
    port: int = 1883
    topic: str = "sensors"
    username: Optional[str]
    password: Optional[str]

class KafkaSettings(BaseSettings):
    class Config:
        env_file = ".env"
        env_prefix = "kafka_"

    bootstrap_servers: str = "kafka:9092"
    topic: str = "sensors"
    producer_interval_ms: int = 1000

class Settings(BaseSettings):
    class Config:
        env_file = ".env"

    mqtt: MqttSettings = MqttSettings()
    kafka: KafkaSettings = KafkaSettings()
    interval_ms: int = 1000
    logging_level: int = 30

@lru_cache()
def get_settings() -> Settings:
    return Settings()