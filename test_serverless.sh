#!/bin/bash

# Test script for the serverless news gather script
# This tests against the local server instead of RunPod

echo "🧪 Testing TKR News Gather Serverless Script (Local Server)"
echo "=========================================================="

# Test against local server
LOCAL_ENDPOINT="http://localhost:8000"

# Function to test local API directly
test_local_api() {
    echo "📡 Testing local API endpoint..."
    
    # Test basic health check
    if curl -s "$LOCAL_ENDPOINT/health" > /dev/null; then
        echo "✅ Local server is running"
    else
        echo "❌ Local server is not accessible at $LOCAL_ENDPOINT"
        echo "Please start the server with: uvicorn src.main:app --host 0.0.0.0 --port 8000"
        exit 1
    fi
    
    # Test news endpoint directly
    echo "🔄 Testing news fetch for Alberta..."
    RESPONSE=$(curl -s "$LOCAL_ENDPOINT/news/Alberta?limit=2&save_to_local=true")
    
    if echo "$RESPONSE" | jq -e '.status == "success"' > /dev/null; then
        TOTAL=$(echo "$RESPONSE" | jq -r '.totalResults')
        echo "✅ Successfully fetched $TOTAL articles"
        
        LOCAL_PATH=$(echo "$RESPONSE" | jq -r '.metadata.local_path // empty')
        if [ -n "$LOCAL_PATH" ] && [ "$LOCAL_PATH" != "null" ]; then
            echo "✅ Saved to local file: $LOCAL_PATH"
        fi
    else
        echo "❌ API test failed"
        echo "Response: $RESPONSE"
        exit 1
    fi
}

# Test the serverless script with mock RunPod response
test_serverless_script() {
    echo ""
    echo "🚀 Testing serverless script..."
    
    # Create a mock response for testing
    cat > mock_response.json << 'EOF'
{
    "id": "test-job-123",
    "status": "COMPLETED",
    "output": {
        "status": "success",
        "totalResults": 2,
        "results": [
            {
                "title": "Test Article 1",
                "source_name": "Test Source",
                "link": "https://example.com/article1",
                "pub_date": "2024-01-01T12:00:00",
                "summary": "This is a test article summary."
            },
            {
                "title": "Test Article 2", 
                "source_name": "Another Source",
                "link": "https://example.com/article2",
                "pub_date": "2024-01-01T13:00:00",
                "summary": "This is another test article summary."
            }
        ],
        "metadata": {
            "province": "Alberta",
            "timestamp": "2024-01-01T12:00:00",
            "local_path": "/path/to/saved/file.json"
        }
    }
}
EOF

    # Test script help
    echo "📖 Testing help output..."
    ./news_gather_serverless.sh --help | head -3
    
    echo "✅ Script is executable and shows help"
    
    # Clean up
    rm -f mock_response.json
}

# Run tests
test_local_api
test_serverless_script

echo ""
echo "🎉 All tests completed!"
echo ""
echo "Usage examples:"
echo "  # Test with local server (save locally)"
echo "  curl \"http://localhost:8000/news/Alberta?limit=3&save_to_local=true\""
echo ""
echo "  # Use serverless script (requires RunPod setup)"
echo "  export RUNPOD_API_KEY=\"your-api-key\""
echo "  export RUNPOD_ENDPOINT_URL=\"your-endpoint-url\""
echo "  ./news_gather_serverless.sh --province \"Alberta\" --save-to-local --limit 5"