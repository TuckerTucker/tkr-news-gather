# 🚀 RunPod Serverless Deployment Guide

## Overview

This guide walks you through deploying the TKR News Gather as a serverless endpoint on RunPod.

## Prerequisites

- RunPod account (sign up at https://runpod.io)
- Docker Hub account (or another container registry)
- Anthropic API key
- Supabase project (optional)

## Step 1: Push Docker Image to Registry

First, tag and push the built image to Docker Hub:

```bash
# Tag the image for Docker Hub
docker tag tkr-news-gather:simple your-dockerhub-username/tkr-news-gather:latest

# Push to Docker Hub
docker push your-dockerhub-username/tkr-news-gather:latest
```

## Step 2: Create RunPod Serverless Endpoint

1. **Login to RunPod**
   - Go to https://runpod.io
   - Sign in to your account

2. **Navigate to Serverless**
   - Click on "Serverless" in the top navigation
   - Click "New Endpoint"

3. **Configure the Endpoint**
   - **Name**: `tkr-news-gather`
   - **Container Image**: `your-dockerhub-username/tkr-news-gather:latest`
   - **Container Registry Credentials**: Add your Docker Hub credentials if image is private

4. **Set Environment Variables**
   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ANTHROPIC_MODEL=claude-3-haiku-20241022
   LLM_TEMP=0.7
   LLM_MAX_TOKENS=200000
   SUPABASE_URL=your_supabase_url_here
   SUPABASE_ANON_KEY=your_supabase_anon_key_here
   LOG_LEVEL=INFO
   ```

5. **Configure Resources**
   - **GPU**: None (CPU only)
   - **Container Disk**: 5GB
   - **Memory**: 4GB
   - **CPU**: 2 vCPUs

6. **Advanced Settings**
   - **Max Workers**: 5
   - **Idle Timeout**: 30 seconds
   - **Execution Timeout**: 600 seconds (10 minutes)

## Step 3: Test the Deployment

Once deployed, you'll get an endpoint URL like:
```
https://api.runpod.ai/v2/your-endpoint-id/runsync
```

### Test with cURL

**Get Provinces:**
```bash
curl -X POST https://api.runpod.ai/v2/your-endpoint-id/runsync \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-runpod-api-key" \
  -d '{
    "input": {
      "action": "get_provinces"
    }
  }'
```

**Get News for Alberta:**
```bash
curl -X POST https://api.runpod.ai/v2/your-endpoint-id/runsync \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-runpod-api-key" \
  -d '{
    "input": {
      "action": "get_news",
      "province": "Alberta",
      "limit": 5,
      "scrape": true
    }
  }'
```

**Process News with AI:**
```bash
curl -X POST https://api.runpod.ai/v2/your-endpoint-id/runsync \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-runpod-api-key" \
  -d '{
    "input": {
      "action": "process_news",
      "articles": [
        {
          "title": "Test Article",
          "content": "This is test content",
          "source_name": "Test Source",
          "link": "https://example.com",
          "wtkr_id": "test-123"
        }
      ],
      "host_type": "anchor",
      "province": "Alberta"
    }
  }'
```

## Step 4: API Actions

Your deployed endpoint supports these actions:

### 1. `get_provinces`
Returns list of all Canadian provinces with metadata.

**Input:**
```json
{
  "input": {
    "action": "get_provinces"
  }
}
```

### 2. `get_news`
Fetches news for a specific province.

**Input:**
```json
{
  "input": {
    "action": "get_news",
    "province": "Alberta",
    "limit": 10,
    "scrape": true
  }
}
```

### 3. `process_news`
Process articles with AI host personalities.

**Input:**
```json
{
  "input": {
    "action": "process_news",
    "articles": [...],
    "host_type": "anchor|friend|newsreel",
    "province": "Alberta"
  }
}
```

### 4. `scrape_urls`
Scrape content from specific URLs.

**Input:**
```json
{
  "input": {
    "action": "scrape_urls",
    "urls": ["https://example.com/article1", "https://example.com/article2"]
  }
}
```

## Step 5: Integration Example

Here's a Python example for integrating with your RunPod endpoint:

```python
import requests
import json

class TKRNewsClient:
    def __init__(self, endpoint_url, api_key):
        self.endpoint_url = endpoint_url
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
    
    def get_provinces(self):
        payload = {
            "input": {
                "action": "get_provinces"
            }
        }
        response = requests.post(self.endpoint_url, 
                               headers=self.headers, 
                               json=payload)
        return response.json()
    
    def get_news(self, province, limit=10, scrape=True):
        payload = {
            "input": {
                "action": "get_news",
                "province": province,
                "limit": limit,
                "scrape": scrape
            }
        }
        response = requests.post(self.endpoint_url, 
                               headers=self.headers, 
                               json=payload)
        return response.json()
    
    def process_news(self, articles, host_type, province):
        payload = {
            "input": {
                "action": "process_news",
                "articles": articles,
                "host_type": host_type,
                "province": province
            }
        }
        response = requests.post(self.endpoint_url, 
                               headers=self.headers, 
                               json=payload)
        return response.json()

# Usage
client = TKRNewsClient(
    endpoint_url="https://api.runpod.ai/v2/your-endpoint-id/runsync",
    api_key="your-runpod-api-key"
)

# Get provinces
provinces = client.get_provinces()
print(f"Available provinces: {len(provinces['output']['provinces'])}")

# Get news for Alberta
news = client.get_news("Alberta", limit=5)
if news['output']['status'] == 'success':
    print(f"Found {news['output']['totalResults']} articles")
    
    # Process with anchor personality
    processed = client.process_news(
        news['output']['results'],
        "anchor",
        "Alberta"
    )
    print(f"Processed {len(processed['output']['articles'])} articles")
```

## Step 6: Monitoring and Scaling

### RunPod Dashboard
- Monitor endpoint usage in the RunPod dashboard
- View logs and performance metrics
- Adjust scaling parameters as needed

### Cost Optimization
- **Idle Timeout**: Keep short (30s) to minimize costs
- **Max Workers**: Start with 5, scale based on usage
- **GPU**: Not needed for this workload

### Performance Tips
- Use `scrape=false` for faster responses when full content isn't needed
- Limit article count for better response times
- Consider caching frequently requested provinces

## Troubleshooting

### Common Issues

1. **Container won't start**
   - Check environment variables are set correctly
   - Verify Docker image is accessible
   - Check RunPod logs for error messages

2. **API timeouts**
   - Increase execution timeout in RunPod settings
   - Reduce article limit or disable scraping
   - Check if external APIs (Anthropic/Supabase) are responding

3. **Memory issues**
   - Increase memory allocation in RunPod
   - Reduce concurrent scraping limit
   - Monitor memory usage in logs

4. **Rate limiting**
   - Anthropic API has rate limits - space out requests
   - Some news sites may block automated requests
   - Consider adding delays between scraping requests

### Debug Mode

Set `LOG_LEVEL=DEBUG` in environment variables for detailed logging.

## Security Considerations

- **API Keys**: Store securely in RunPod environment variables
- **Rate Limiting**: Implement client-side rate limiting
- **Content Filtering**: Be aware that scraped content may contain inappropriate material
- **Compliance**: Ensure scraping practices comply with site terms of service

## Support

- RunPod Documentation: https://docs.runpod.io
- Anthropic API Docs: https://docs.anthropic.com
- For issues with this deployment, check the project's GitHub repository