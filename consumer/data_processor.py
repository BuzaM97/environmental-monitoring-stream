#!/usr/bin/env python3
"""
🔄 Data Processor Consumer - Process Kafka messages and write to InfluxDB

Receives messages from Kafka topic: iot_sensor_data
Processes and writes data to InfluxDB.
"""

import json
import logging
import os
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - Data Processor - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataProcessor:
    """Data processor from Kafka to InfluxDB"""
    
    def __init__(self):
        """Initialize"""
        # Kafka settings
        self.kafka_broker = os.getenv('KAFKA_BROKER', 'localhost:9092')
        self.iot_topic = os.getenv('IOT_TOPIC', 'iot_sensor_data')
        self.sentinel_topic = os.getenv('SENTINEL_TOPIC', 'sentinel_data')
        
        # InfluxDB settings
        self.influx_url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
        self.influx_token = os.getenv('INFLUXDB_TOKEN', 'iot_admin_token_secret123')
        self.influx_org = os.getenv('INFLUXDB_ORG', 'iot_org')
        self.influx_bucket = os.getenv('INFLUXDB_BUCKET', 'iot_data')
        
        self.consumer = None
        self.influx_client = None
        self.write_api = None
        
        # Statistics
        self.stats = {
            'iot_messages': 0,
            'sentinel_messages': 0,
            'influx_writes': 0,
            'errors': 0
        }
    
    def connect_kafka(self):
        """Connect to Kafka"""
        try:
            self.consumer = KafkaConsumer(
                self.iot_topic,
                self.sentinel_topic,
                bootstrap_servers=[self.kafka_broker],
                auto_offset_reset='earliest',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
                group_id='data-processor-group'
            )
            logger.info(f"Connected to Kafka: {self.kafka_broker}")
            logger.info(f"   Topics: {self.iot_topic}, {self.sentinel_topic}")
        except Exception as e:
            logger.error(f"Kafka connection error: {e}")
            raise
    
    def connect_influxdb(self):
        """Connect to InfluxDB"""
        try:
            self.influx_client = InfluxDBClient(
                url=self.influx_url,
                token=self.influx_token,
                org=self.influx_org
            )
            
            # Health check
            health = self.influx_client.health()
            logger.info(f"Connected to InfluxDB")
            logger.info(f"URL: {self.influx_url}")
            logger.info(f"Org: {self.influx_org}")
            logger.info(f"Bucket: {self.influx_bucket}")
            logger.info(f"Status: {health.status}")
            
            self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
        except Exception as e:
            logger.error(f"InfluxDB connection error: {e}")
            raise
    
    def process_iot_data(self, message):
        """Process IoT data"""
        try:
            data = message.value
            
            # Convert timestamp to nanosecond format for InfluxDB
            # InfluxDB requires nanosecond precision
            timestamp_str = data.get('timestamp', datetime.now().isoformat())
            
            # Parse ISO format and convert to Unix timestamp in nanoseconds
            # Remove Z if present and parse
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1]
            
            # Use fromisoformat (Python 3.7+)
            from datetime import datetime as dt_class
            ts = dt_class.fromisoformat(timestamp_str)
            # Convert to nanoseconds since epoch
            timestamp_ns = int(ts.timestamp() * 1e9)
            
            # Use Line Protocol format instead of Point object
            line_protocol = (
                f'iot_sensor,'
                f'sensor_id={data.get("sensor_id", "unknown")},'
                f'location={data.get("location", "unknown")} '
                f'soil_moisture={float(data.get("soil_moisture", 0))},'
                f'water_level={float(data.get("water_level", 0))},'
                f'temperature={float(data.get("temperature", 0))} '
                f'{timestamp_ns}'
            )
            
            self.write_api.write(bucket=self.influx_bucket, record=line_protocol)
            self.stats['iot_messages'] += 1
            self.stats['influx_writes'] += 1
            
            logger.info(
                f"📊 IoT adat feldolgozva | "
                f"Moisture: {data['soil_moisture']}% | "
                f"WaterLevel: {data['water_level']}mm | "
                f"Temp: {data['temperature']}°C"
            )
            return True
        except Exception as e:
            logger.error(f"IoT processing error: {e}")
            self.stats['errors'] += 1
            return False
    
    def process_sentinel_data(self, message):
        """Process Sentinel satellite data - each interval separately"""
        try:
            data = message.value
            
            # Extract data from Sentinel response
            if 'raw_response' not in data:
                logger.warning("Sentinel message missing raw_response field")
                return False
            
            sentinel_payload = data.get('raw_response', {})
            aoi_bbox = data.get('aoi_bbox', [0, 0, 0, 0])
            
            # Parse main timestamp
            timestamp_str = data.get('timestamp', datetime.now().isoformat())
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1]
            
            from datetime import datetime as dt_class
            ts = dt_class.fromisoformat(timestamp_str)
            timestamp_ns = int(ts.timestamp() * 1e9)
            
            # Extract intervals from response
            intervals = sentinel_payload.get('data', [])
            
            if not intervals:
                logger.warning("No intervals found in Sentinel response")
                return False
            
            # Process each interval separately
            for idx, interval in enumerate(intervals):
                try:
                    # Get sample count (data points)
                    sample_count = interval.get('outputs', {}).get('data', {}).get('bands', {}).get('B0', {}).get('stats', {}).get('sampleCount', 0)
                    
                    # Get SCL as cloud coverage (B5 from evalscript, 0-10 scale converted to 0-100%)
                    scl_band = interval.get('outputs', {}).get('data', {}).get('bands', {}).get('B5', {}).get('stats', {})
                    scl_mean = scl_band.get('mean', 0)
                    scl_max = scl_band.get('max', 0)
                    
                    # Convert SCL from 0-10 scale to 0-100% cloud coverage
                    cloud_coverage = scl_mean * 10.0
                    
                    # Get interval date range
                    interval_from = interval.get('interval', {}).get('from', 'N/A')
                    interval_to = interval.get('interval', {}).get('to', 'N/A')
                    
                    if interval_from != 'N/A' and interval_from.endswith('Z'):
                        interval_from = interval_from[:-1]
                    if interval_to != 'N/A' and interval_to.endswith('Z'):
                        interval_to = interval_to[:-1]
                    
                    interval_ts = dt_class.fromisoformat(interval_from)
                    interval_date = interval_ts.date().isoformat()
                    interval_timestamp_ns = int(interval_ts.timestamp() * 1e9)
                    
                    # Only process indices if CLEAR (scl < 5)
                    should_record_indices = scl_mean < 5
                    
                    # Get indices only if CLEAR (scl < 5)
                    ndvi_value = None
                    ndwi_value = None
                    ndmi_value = None
                    
                    if sample_count > 0 and should_record_indices:
                        data_bands = interval.get('outputs', {}).get('data', {}).get('bands', {})
                        
                        # Get pre-calculated indices from evalscript
                        # B0: NDVI, B1: NDWI, B2: NDMI
                        ndvi_value = data_bands.get('B0', {}).get('stats', {}).get('mean', None)
                        ndwi_value = data_bands.get('B1', {}).get('stats', {}).get('mean', None)
                        ndmi_value = data_bands.get('B2', {}).get('stats', {}).get('mean', None)
                    
                    # Determine quality based on SCL
                    quality = "cloudy" if scl_mean >= 5 else "clear"
                    
                    # Write to InfluxDB - each interval as separate point
                    fields = "cloud_coverage=" + str(round(cloud_coverage, 2)) + ",scl_mean=" + str(round(scl_mean, 2)) + ",scl_max=" + str(round(scl_max, 2))
                    
                    # Only add indices if CLEAR (scl < 5)
                    if ndvi_value is not None:
                        fields = fields + ",ndvi=" + str(round(ndvi_value, 6))
                    
                    if ndwi_value is not None:
                        fields = fields + ",ndwi=" + str(round(ndwi_value, 6))
                    
                    if ndmi_value is not None:
                        fields = fields + ",ndmi=" + str(round(ndmi_value, 6))
                    
                    tags = "sentinel_data,region=szentes,interval_index=" + str(idx) + ",date=" + interval_date + ",data_source=sentinel-2-l2a,quality=" + quality
                    line_protocol = tags + " " + fields + " " + str(interval_timestamp_ns)
                    
                    self.write_api.write(bucket=self.influx_bucket, record=line_protocol)
                    self.stats['sentinel_messages'] += 1
                    self.stats['influx_writes'] += 1
                    
                    ndvi_str = str(round(ndvi_value, 6)) if ndvi_value else "N/A"
                    ndwi_str = str(round(ndwi_value, 6)) if ndwi_value else "N/A"
                    ndmi_str = str(round(ndmi_value, 6)) if ndmi_value else "N/A"
                    cloud_str = str(round(cloud_coverage, 1))
                    log_msg = "[SENTINEL-INTERVAL " + str(idx) + "] " + str(interval_from) + " to " + str(interval_to) + " | Quality: " + str(quality) + " | Cloud: " + cloud_str + "% | NDVI: " + ndvi_str + " | NDWI: " + ndwi_str + " | NDMI: " + ndmi_str
                    logger.info(log_msg)
                    
                except Exception as e:
                    logger.error("Error processing interval " + str(idx) + ": " + str(e))
                    self.stats['errors'] += 1
                    continue
            
            return True
        except Exception as e:
            logger.error("Sentinel processing error: " + str(e))
            self.stats['errors'] += 1
            return False
    
    def process_message(self, message):
        """Route message to appropriate processor based on topic"""
        if message.topic == self.iot_topic:
            return self.process_iot_data(message)
        elif message.topic == self.sentinel_topic:
            return self.process_sentinel_data(message)
        else:
            logger.warning(f"Unknown topic: {message.topic}")
            return False
    
    def print_stats(self):
        """Print statistics"""
        logger.info(
                f"\n📈 Statistics:\n"
                f"   IoT messages: {self.stats['iot_messages']}\n"
                f"   Sentinel messages: {self.stats['sentinel_messages']}\n"
                f"   InfluxDB writes: {self.stats['influx_writes']}\n"
                f"   Errors: {self.stats['errors']}")
    
    def run(self):
        """Processing loop"""
        logger.info("🚀 Data Processor Consumer started")
        
        try:
            self.connect_kafka()
            self.connect_influxdb()
            
            logger.info("✅ Receiving messages...")
            
            for message in self.consumer:
                self.process_message(message)
        
        except KeyboardInterrupt:
            logger.info("\n⏸️  Consumer stopped (Ctrl+C)")
            self.print_stats()
        except Exception as e:
            logger.error(f"Error: {e}")
            self.stats['errors'] += 1
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup"""
        if self.consumer:
            self.consumer.close()
            logger.info("✅ Kafka consumer closed")
        
        if self.influx_client:
            self.influx_client.close()
            logger.info("✅ InfluxDB client closed")


if __name__ == "__main__":
    processor = DataProcessor()
    processor.run()
