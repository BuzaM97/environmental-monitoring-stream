import json
import logging
import requests
import time
from datetime import datetime, timedelta
from kafka import KafkaProducer
from dotenv import load_dotenv
import os
from apscheduler.schedulers.background import BackgroundScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - Sentinel API Producer - %(levelname)s - %(message)s'
)


class SentinelAPIProducer:
    """Sentinel-2 Satellite Data Producer"""

    def __init__(self):
        """Initialization"""
        load_dotenv()
        self.kafka_broker = os.getenv('KAFKA_BROKER', 'localhost:9092')
        self.topic = os.getenv('SENTINEL_TOPIC', 'sentinel_data')
        
        # OAuth2 Credentials
        self.client_id = os.getenv('SENTINEL_CLIENT_ID')
        self.client_secret = os.getenv('SENTINEL_CLIENT_SECRET')
        self.access_token = None
        self.producer = None
        
        # Sentinel Hub API endpoints
        self.token_url = "https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token"
        self.api_url = "https://services.sentinel-hub.com/api/v1/statistics"
        
        # AOI (Area of Interest) - Szentes, Hungary region
        self.bbox = [17.684968,
                     46.883896,
                     17.738526,
                     46.903838 ]
        
        # Evalscript with NDVI, NDMI, and raw band values
        self.evalscript = """//VERSION=3
function setup() {
  return {
    input: [{
      bands: [
        "B03",
        "B04",
        "B08",
        "B11",
        "SCL",
        "dataMask"
      ]
    }],
    output: [
      {
        id: "data",
        bands: 6
      },
      {
        id: "scl",
        sampleType: "INT8",
        bands: 1
      },
      {
        id: "dataMask",
        bands: 1
      }]
  };
}

function evaluatePixel(samples) {
    // NDVI - Normalized Difference Vegetation Index
    let ndvi = (samples.B08 - samples.B04) / (samples.B08 + samples.B04);
    
    // NDMI - Normalized Difference Moisture Index
    let ndmi = (samples.B08 - samples.B11) / (samples.B08 + samples.B11);
    
    // NDWI - Normalized Difference Water Index
    let ndwi = (samples.B08 - samples.B03) / (samples.B08 + samples.B03);
    
    // SCL as cloud coverage indicator (0-10 scale, will be converted to 0-100%)
    let scl_value = samples.SCL;
    
    return {
        // B0: NDVI, B1: NDWI, B2: NDMI, B3: raw NIR (B08), B4: raw SWIR (B11), B5: SCL (cloud coverage)
        data: [ndvi, ndwi, ndmi, samples.B08, samples.B11, scl_value],
        dataMask: [samples.dataMask],
        scl: [samples.SCL]
    };
}
"""

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

    def validate_token(self):
        """Validate that OAuth2 credentials are configured"""
        if not self.client_id or not self.client_secret:
            logging.error("SENTINEL_CLIENT_ID or SENTINEL_CLIENT_SECRET not found in environment variables!")
            raise ValueError("Missing Sentinel Hub OAuth2 credentials in .env file")
        logging.info("Sentinel Hub OAuth2 credentials found")

    def get_access_token(self):
        """Get OAuth2 access token from Sentinel Hub"""
        try:
            self.validate_token()
            
            logging.info("Fetching OAuth2 token from Sentinel Hub...")
            
            response = requests.post(
                self.token_url,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret
                },
                timeout=10
            )
            
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            
            logging.info(f"OAuth2 token obtained successfully. Expires in {token_data.get('expires_in')} seconds")
            return self.access_token
            
        except Exception as e:
            logging.error(f"Error fetching OAuth2 token: {e}")
            raise

    def build_request_payload(self):
        """Build the Statistics API request payload"""
        # Calculate date range: last 30 days
        to_date = datetime.utcnow()
        from_date = to_date - timedelta(days=360)
        
        payload = {
            "input": {
                "bounds": {
                    "bbox": self.bbox
                },
                "data": [
                    {
                        "dataFilter": {},
                        "type": "sentinel-2-l2a"
                    }
                ]
            },
            "aggregation": {
                "timeRange": {
                    "from": from_date.isoformat() + "Z",
                    "to": to_date.isoformat() + "Z"
                },
                "aggregationInterval": {
                    "of": "P1D"  # 1-day aggregation
                },
                "width": 512,
                "height": 464,
                "evalscript": self.evalscript
            },
            "calculations": {
                "default": {}
            }
        }
        return payload

    def fetch_sentinel_data(self):
        """Fetch data from Sentinel Hub Statistics API"""
        try:
            # Get fresh access token
            if not self.access_token:
                self.get_access_token()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            payload = self.build_request_payload()
            
            logging.info(f"Sending request to Sentinel Hub API for AOI bbox: {self.bbox}")
            
            # DEBUG: Print request details
            print("\n" + "="*60)
            print("SENTINEL HUB STATISTICS API REQUEST")
            print("="*60)
            print(f"URL: {self.api_url}")
            print(f"Method: POST")
            print(f"Headers: {headers}")
            print(f"Payload: {json.dumps(payload, indent=2, default=str)}")
            print("="*60 + "\n")
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=90
            )
            
            # DEBUG: Print response details
            print("RESPONSE")
            print("="*60)
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Body:\n{response.text[:500]}...")
            print("="*60 + "\n")
            
            response.raise_for_status()
            
            data = response.json()
            logging.info(f"Successfully retrieved Sentinel data. Status code: {response.status_code}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching from Sentinel Hub API: {e}")
            return None
        except ValueError as e:
            logging.error(f"Validation error: {e}")
            return None

    def send_data(self, data):
        """Send data to Kafka topic"""
        try:
            future = self.producer.send(self.topic, value=data)
            result = future.get(timeout=10)
            logging.info(f"Data sent to Kafka topic '{self.topic}'")
            return True
        except Exception as e:
            logging.error(f"Error sending data to Kafka: {e}")
            return False

    def process_and_send(self):
        """Fetch Sentinel data and send to Kafka"""
        try:
            sentinel_data = self.fetch_sentinel_data()
            print(json.dumps(sentinel_data, indent=2))  # For debugging
            if sentinel_data is None:
                logging.warning("Failed to fetch Sentinel data, skipping send")
                return
            
            # Prepare message for Kafka
            message = {
                "timestamp": datetime.now().isoformat(),
                "source": "sentinel-2-l2a",
                "aoi_bbox": self.bbox,
                "data_points": len(sentinel_data.get("data", [])) if isinstance(sentinel_data.get("data"), list) else 1,
                "raw_response": sentinel_data
            }
            
            if self.send_data(message):
                logging.info("Sentinel data successfully processed and sent to Kafka")
            else:
                logging.error("Failed to send Sentinel data to Kafka")
                
        except Exception as e:
            logging.error(f"Error in process_and_send: {e}")

    def run_scheduled(self):
        """Run data fetching on a schedule"""
        self.connect()
        
        scheduler = BackgroundScheduler()
        # Schedule to run daily at 9:00 AM
        scheduler.add_job(self.process_and_send, 'cron', hour=9, minute=0)
        scheduler.start()
        
        logging.info("Sentinel API Producer started with daily schedule (9:00 AM)")
        logging.info(f"Kafka topic: {self.topic}")
        logging.info(f"AOI bbox: {self.bbox}")
        
        try:
            while True:
                pass
        except KeyboardInterrupt:
            logging.info("Shutting down Sentinel API Producer...")
            scheduler.shutdown()
            if self.producer:
                self.producer.close()

    def run_once(self):
        """Run data fetching once (for testing)"""
        self.connect()
        logging.info("Sentinel API Producer running in one-shot mode")
        self.process_and_send()
        if self.producer:
            self.producer.close()


if __name__ == "__main__":
    producer = SentinelAPIProducer()
    
    # Uncomment one of the following:
    # For scheduled execution:
    #producer.run_scheduled()
    
    # For one-time execution (testing):
    producer.run_once()
