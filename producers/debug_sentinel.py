import json
from sentinel_api import SentinelAPIProducer

if __name__ == "__main__":
    producer = SentinelAPIProducer()
    
    print("Testing Sentinel Hub API with OAuth2 authentication...")
    print("=" * 70)
    
    try:
        # Get access token once
        token = producer.get_access_token()
        print(f"✓ Access token obtained: {token[:50]}...\n")
        
        # Process both fields one after another
        for field_name, field_config in producer.fields.items():
            print("\n" + "=" * 70)
            print(f"🌾 Processing {field_name}...")
            print("=" * 70)
            
            bbox = field_config["bbox"]
            print(f"   Bbox: {bbox}\n")
            
            try:
                # Fetch Sentinel data for this field
                data = producer.fetch_sentinel_data(field_name, bbox)
                
                if data:
                    print(f"✓ Response from Sentinel API for {field_name}:")
                    print(json.dumps(data, indent=2, default=str))
                else:
                    print(f"✗ Failed to fetch data from API for {field_name}")
                    
            except Exception as e:
                print(f"✗ Error fetching data for {field_name}: {e}")
                import traceback
                traceback.print_exc()
            
            print("\n---")
        
        print("\n" + "=" * 70)
        print("✓ All fields processed successfully")
        print("=" * 70)
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

