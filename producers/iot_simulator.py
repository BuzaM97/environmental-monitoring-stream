
import json
import time
import logging
import random
from datetime import datetime
from kafka import KafkaProducer
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - IoT Simulator - %(levelname)s - %(message)s'
)

class IoTSimulator:
    """IoT Sensor Simulator"""

      
    def __init__(self):
        """Initialization"""
        load_dotenv() 
        self.kafka_broker = os.getenv('KAFKA_BROKER', 'localhost:9092')
        self.topic = os.getenv('IOT_TOPIC', 'iot_sensor_data') # Default topic name
        self.sensor_id = 'sensor-001'   # Unique sensor ID
        self.interval = 30               # Time interval between messages (seconds)
        self.location = 'greenhouse' # Sensor location (e.g., field, greenhouse)
        self.producer = None
        self.base_moisture = 65.0
        self.base_water_level = 1200.0
        self.base_temperature = 22.0

    def connect(self):
        """Connect to Kafka Producer"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=[self.kafka_broker],
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                request_timeout_ms=10000,
                retries=3
            )
            logging.info("Successfully connected to Kafka Producer.")
        except Exception as e:
            logging.error(f"Error connecting to Kafka Producer: {e}")
            raise

    def send_data(self, data):
        """Send data to Kafka topic"""
        try:
            future = self.producer.send(self.topic, value=data)
            result = future.get(timeout=10)
            return True
        except Exception as e:
            logging.error(f"Error sending data to Kafka: {e}")
            return False
        
    def generate_sensor_data(self):
        """Generate sensor data"""
        # Simulate realistic fluctuations
        moisture = self.base_moisture + random.uniform(-5, 5)
        water_level = self.base_water_level + random.uniform(-20, 20)
        temperature = self.base_temperature + random.uniform(-2, 2)
        
        # Ensure realistic values
        moisture = max(0, min(100, moisture))
        water_level = max(0, min(2000, water_level))
        temperature = max(0, min(40, temperature))
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "sensor_id": self.sensor_id,
            "location": self.location,
            "soil_moisture": round(moisture, 2),
            "water_level": round(water_level, 2),
            "temperature": round(temperature, 2),
            "unit_moisture": "%",
            "unit_water_level": "mm",
            "unit_temperature": "°C"
        }
        
        return data
    
    def run_simulation(self):
        """Simulation loop"""
        logging.info("IoT Simulator started")
        logging.info(f"Topic: {self.topic}")
        logging.info(f"Sensor ID: {self.sensor_id}")
        logging.info(f"Interval: {self.interval} seconds")
        logging.info(f"Location: {self.location}")
        
        try:
            self.connect()
            
            counter = 0
            while True:
                counter += 1
                data = self.generate_sensor_data()
                
                if self.send_data(data):
                    logging.info(f"[{counter}] Message sent: {data['sensor_id']}")
                else:
                    logging.warning(f"[{counter}] Message sending failed, retrying...")
                
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            logging.info("Simulation stopped (Ctrl+C)")
        except Exception as e:
            logging.error(f"Error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup"""
        if self.producer:
            self.producer.close()
            logging.info("Kafka producer closed")

if __name__ == "__main__":
    simulator = IoTSimulator()
    simulator.run_simulation()