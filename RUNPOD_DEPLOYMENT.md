# TKR News Gather - RunPod Deployment Guide
Generated: 2025-06-05 12:32:29

## 🐳 Docker Image
Your image has been pushed to: `tuckertucker/tkr-news-gather:latest`

## ✅ Template Created Successfully!
- **Template ID**: `rxaw4dxqtm`
- **Template Name**: `tkr-news-gatherer-template`

Your template is ready! Use it to create a serverless endpoint in the RunPod dashboard.

## ✅ Endpoint Created Successfully!
- **Endpoint ID**: `d0w22s1p9xfvnt`
- **Endpoint URL**: `https://api.runpod.io/v2/d0w22s1p9xfvnt/runsync`

Your endpoint is ready to use! Skip to the "Testing Your Deployment" section below.

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
Your endpoint URL is:
`https://api.runpod.io/v2/d0w22s1p9xfvnt/runsync`

### Sample Test Requests

**Get Provinces:**
```bash
curl -X POST https://api.runpod.io/v2/d0w22s1p9xfvnt/runsync \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer rpa_173ARN..." \
  -d '{
    "input": {
      "action": "get_provinces"
    }
  }'
```

**Get News for Alberta:**
```bash
curl -X POST https://api.runpod.io/v2/d0w22s1p9xfvnt/runsync \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer rpa_173ARN..." \
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
curl -X POST https://api.runpod.io/v2/d0w22s1p9xfvnt/runsync \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer rpa_173ARN..." \
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

### Step 1: Template Already Created ✅
Your template `rxaw4dxqtm` is ready to use.

### Step 2: Create Serverless Endpoint
1. **Navigate to Serverless**: Click "Serverless" in the top menu
2. **Create New Endpoint**: Click "New Endpoint"
3. **Select Template**: Choose your template `rxaw4dxqtm`
4. **Configure Scaling**:
   - Max Workers: 5
   - Idle Timeout: 30 seconds
   - Execution Timeout: 600 seconds
5. **Deploy**: Click "Deploy" and wait for the endpoint to be ready
6. **Copy Endpoint ID**: Save the endpoint ID for testing

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
- TKR News Gather Issues: Create an issue in the project repository
