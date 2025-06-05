# TKR News Gatherer - RunPod Deployment Guide
Generated: 2025-06-05 12:01:19

## 🐳 Docker Image
Your image has been pushed to: `tuckertucker/tkr-news-gather:latest`

## 🚀 RunPod Endpoint Configuration

### Basic Settings
- **Name**: `tkr-news-gatherer`
- **Container Image**: `tuckertucker/tkr-news-gather:latest`
- **Container Registry**: Docker Hub (public)

### Resource Configuration
- **Memory**: 4GB
- **CPU**: 2 vCPUs
- **Storage**: 5GB
- **GPU**: None (CPU only)

### Scaling Configuration  
- **Max Workers**: 5
- **Idle Timeout**: 30 seconds
- **Execution Timeout**: 600 seconds

### Environment Variables
Add these environment variables in the RunPod dashboard:

```bash
# Required - Anthropic API
ANTHROPIC_API_KEY=sk-ant-a...

# Security (from generated credentials)
JWT_SECRET_KEY=brMjzgIm8b4cgffI97uSSU8gchXEDN9BhPobdjQXtA8
API_KEYS=tkr_TO1qOfaHteSXODhgJckp6FtNePNaLALlxnICV1OJ0wI,tkr_WcvBubSP6w5BkaJsgNutY14PEByToD08mzOCaUBxzWI,tkr_2vRqFJAfFRyBhXvMkWHIEuYUb0_FfWqUS4Ncgs1RNO8

# Database - Supabase
SUPABASE_URL=https://ulxcrneqocsjpirdngnd.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...

# Optional Configuration
LOG_LEVEL=INFO
ANTHROPIC_MODEL=claude-3-haiku-20241022
LLM_TEMP=0.7
LLM_MAX_TOKENS=200000
```

## 🧪 Testing Your Deployment

### Test Endpoints
Once deployed, your endpoint URL will be:
`https://api.runpod.ai/v2/YOUR-ENDPOINT-ID/runsync`

### Sample Test Requests

**Get Provinces:**
```bash
curl -X POST https://api.runpod.ai/v2/YOUR-ENDPOINT-ID/runsync \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR-RUNPOD-API-KEY" \
  -d '{
    "input": {
      "action": "get_provinces"
    }
  }'
```

**Get News for Alberta:**
```bash
curl -X POST https://api.runpod.ai/v2/YOUR-ENDPOINT-ID/runsync \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR-RUNPOD-API-KEY" \
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
curl -X POST https://api.runpod.ai/v2/YOUR-ENDPOINT-ID/runsync \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR-RUNPOD-API-KEY" \
  -d '{
    "input": {
      "action": "fetch_and_process",
      "province": "Alberta",
      "host_type": "anchor",
      "limit": 3,
      "scrape": true
    }
  }'
```

## 📋 Manual RunPod Setup Steps

1. **Login to RunPod**: Go to https://runpod.io and sign in
2. **Navigate to Serverless**: Click "Serverless" in the top menu
3. **Create New Endpoint**: Click "New Endpoint"
4. **Configure Endpoint**:
   - Name: `tkr-news-gatherer`
   - Container Image: `tuckertucker/tkr-news-gather:latest`
   - Environment Variables: Copy from the section above
   - Resources: Set as specified in Resource Configuration
5. **Deploy**: Click "Deploy" and wait for the endpoint to be ready
6. **Test**: Use the sample requests above to test your deployment

## 🔒 Security Notes

- Store your RunPod API key securely
- The JWT and API keys have been generated for security
- Consider rotating credentials regularly
- Monitor usage and costs in the RunPod dashboard

## 🆘 Troubleshooting

If your deployment fails:
1. Check the RunPod logs for error messages
2. Verify all environment variables are set correctly
3. Ensure your Docker image is public and accessible
4. Test the image locally first: `docker run -p 8000:8000 --env-file .env tuckertucker/tkr-news-gather:latest`

## 📞 Support

- RunPod Documentation: https://docs.runpod.io
- TKR News Gatherer Issues: Create an issue in the project repository
