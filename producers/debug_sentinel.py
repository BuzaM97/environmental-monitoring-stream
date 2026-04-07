import json
from sentinel_api import SentinelAPIProducer

if __name__ == "__main__":
    producer = SentinelAPIProducer()
    
    print("Testing Sentinel Hub API with OAuth2 authentication...")
    print("-" * 50)
    
    try:
        # Get access token
        token = producer.get_access_token()
        print(f"✓ Access token obtained: {token[:50]}...\n")
        
        # Fetch Sentinel data
        data = producer.fetch_sentinel_data()
        
        if data:
            print("✓ Response from Sentinel API:")
            print(json.dumps(data, indent=2, default=str))
        else:
            print("✗ Failed to fetch data from API")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

