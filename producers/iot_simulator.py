
import json
import time
import logging
import random
import math
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
        self.topic = os.getenv('IOT_TOPIC', 'iot_sensor_data')
        self.sensor_id = 'sensor-001'
        self.interval = 1800  # 30 minutes in seconds
        self.location = 'greenhouse'
        self.producer = None
        self.base_moisture = 65.0
        self.base_water_level = 1200.0
        self.base_temperature = 22.0
        self.moisture_trend = 0
        self.last_irrigation = 0

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
    
    def calculate_daily_temperature(self):
        """Calculate temperature based on time of day (daily cycle)"""
        now = datetime.now()
        hour = now.hour + now.minute / 60.0
        
        # Temperature curve: Cold at night, warm during day, cool evening
        daily_offset = 8 * math.sin((hour - 6) * math.pi / 12)
        temp = self.base_temperature + daily_offset
        temp += random.uniform(-1, 1)
        
        return round(max(0, min(40, temp)), 2)
    
    def simulate_irrigation(self):
        """Simulate irrigation: randomly water, then moisture decreases"""
        if random.random() < 0.2:
            self.moisture_trend = 20
            self.last_irrigation = 0
            logging.info("Irrigation triggered")
        
        if self.moisture_trend > 0:
            self.moisture_trend -= 2.5
        
        self.last_irrigation += 0.5
        if self.last_irrigation > 48:
            self.last_irrigation = 48
        
    def generate_sensor_data(self):
        """Generate sensor data"""
        # Apply irrigation simulation
        self.simulate_irrigation()
        
        # Simulate realistic fluctuations
        moisture = self.base_moisture + self.moisture_trend
        moisture -= self.last_irrigation * 0.5
        moisture += random.uniform(-3, 3)
        
        water_level = self.base_water_level
        if self.moisture_trend > 0:
            water_level += self.moisture_trend * 5
        water_level -= self.last_irrigation * 10
        water_level += random.uniform(-50, 50)
        
        temperature = self.calculate_daily_temperature()
        
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
            "unit_temperature": "C"
        }
        
        return data
    
    def run_simulation(self):
        """Simulation loop"""
        logging.info("IoT Simulator started")
        logging.info(f"Topic: {self.topic}")
        logging.info(f"Sensor ID: {self.sensor_id}")
        logging.info(f"Interval: {self.interval} seconds (30 minutes)")
        logging.info(f"Location: {self.location}")
        
        try:
            self.connect()
            
            counter = 0
            while True:
                counter += 1
                data = self.generate_sensor_data()
                
                if self.send_data(data):
                    logging.info(
                        f"[{counter}] Moisture: {data['soil_moisture']:6.1f}% | "
                        f"Water: {data['water_level']:7.0f}mm | "
                        f"Temp: {data['temperature']:5.1f}C"
                    )
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