"""
Test script for the Daana Ingestion Service
Run this after starting the service to verify it's working correctly
"""
import requests
import sys


def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check endpoint...")
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            print(f"   Service: {data['service']}")
            print(f"   Version: {data['version']}")
            print(f"   OpenAI Configured: {data['openai_configured']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to service. Is it running?")
        print("   Start it with: python main.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_schema_endpoint():
    """Test the schema endpoint"""
    print("\n🔍 Testing schema endpoint...")
    try:
        response = requests.get("http://localhost:8000/schema")
        if response.status_code == 200:
            data = response.json()
            tables = data['tables']
            print(f"✅ Schema endpoint working")
            print(f"   Available tables: {', '.join(tables)}")
            return True
        else:
            print(f"❌ Schema endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_convert_endpoint():
    """Test the convert endpoint with sample CSV"""
    print("\n🔍 Testing convert endpoint...")
    try:
        # Check if test file exists
        try:
            with open('test_sample.csv', 'rb') as f:
                files = {'file': ('test_sample.csv', f, 'text/csv')}
                data = {'target_table': 'units'}
                
                response = requests.post(
                    "http://localhost:8000/convert",
                    files=files,
                    data=data,
                    params={'return_metadata': 'true'}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print("✅ Convert endpoint working")
                    print(f"   Mapped columns: {result['mapped_count']}")
                    print(f"   Unmapped columns: {result['unmapped_count']}")
                    print(f"   Column mapping:")
                    for orig, target in result['column_mapping'].items():
                        print(f"      {orig} → {target}")
                    if result['unmapped_columns']:
                        print(f"   Unmapped: {', '.join(result['unmapped_columns'])}")
                    return True
                else:
                    print(f"❌ Convert failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return False
        except FileNotFoundError:
            print("⚠️  test_sample.csv not found, skipping conversion test")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Testing Daana Ingestion Service\n")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health_check()))
    results.append(("Schema Endpoint", test_schema_endpoint()))
    results.append(("Convert Endpoint", test_convert_endpoint()))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:\n")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} - {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 All tests passed! Service is working correctly.")
        print("\n📚 Next steps:")
        print("   - Visit http://localhost:8000/docs for API documentation")
        print("   - Upload your own CSV files using the /convert endpoint")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
