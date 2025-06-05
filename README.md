# TKR News Gather

A Python-based news collection and AI processing system for Canadian provincial news with multiple host personalities.

## Features

- 🇨🇦 **Canadian Provincial News**: Fetches news from all 13 Canadian provinces and territories
- 🤖 **AI Host Personalities**: Process news with 3 different AI personalities (anchor, friend, newsreel)
- 🕷️ **Web Scraping**: Full article content extraction using Crawl4ai
- 🗄️ **Database Integration**: Optional Supabase PostgreSQL storage
- 🚀 **FastAPI**: Modern async REST API
- 🐳 **Docker Ready**: Containerized for easy deployment
- ☁️ **RunPod Compatible**: Serverless deployment support

## AI Host Personalities

1. **Professional News Anchor**: Authoritative, clear, and objective delivery
2. **Friendly Neighbor**: Warm, conversational, and relatable style
3. **1940s Newsreel**: Dramatic, theatrical, and vintage announcer

## Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd tkr-news-gather

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### 2. Required Environment Variables

```bash
# Anthropic API (Required)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Supabase (Required for secure API - includes authentication)
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here

# Security (Optional but recommended)
JWT_SECRET_KEY=your_jwt_secret_key_here
API_KEYS=your_api_key1,your_api_key2
```

### 3. Installation Options

#### Option A: Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start the local server
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Or use the startup script
chmod +x start_server.sh
./start_server.sh
```

#### Option B: Docker
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build Docker image manually
docker build -t tkr-news-gather .
docker run -p 8000:8000 --env-file .env tkr-news-gather
```

## Usage

### 🖥️ Local Server Usage

The FastAPI server runs on `http://localhost:8000` with automatic documentation at `/docs`.

#### Basic News Fetching
```bash
# Get 5 articles for Alberta
curl "http://localhost:8000/news/Alberta?limit=5"

# Get news with full content scraping
curl "http://localhost:8000/news/Alberta?limit=5&scrape=true"

# Save to local filesystem
curl "http://localhost:8000/news/Alberta?limit=5&save_to_local=true"

# Save to Supabase database
curl "http://localhost:8000/news/Alberta?limit=5&save_to_db=true"

# Combine options: scrape, save locally and to database
curl "http://localhost:8000/news/Alberta?limit=10&scrape=true&save_to_local=true&save_to_db=true"
```

#### AI Processing
```bash
# Fetch and process with anchor personality
curl -X POST "http://localhost:8000/process/Alberta/anchor?limit=3"

# Process with friend personality
curl -X POST "http://localhost:8000/process/Alberta/friend?limit=3"

# Process with newsreel personality
curl -X POST "http://localhost:8000/process/Alberta/newsreel?limit=3"
```

#### Local Storage Management
```bash
# List all locally saved sessions
curl "http://localhost:8000/local/sessions"

# Get sessions for specific province
curl "http://localhost:8000/local/sessions?province=Alberta"

# Get latest session for a province
curl "http://localhost:8000/local/sessions/Alberta/latest"

# Clean up old sessions (delete older than 30 days)
curl -X DELETE "http://localhost:8000/local/sessions/old?days_to_keep=30"
```

#### Other Endpoints
```bash
# Get all available provinces
curl "http://localhost:8000/provinces"

# Health check
curl "http://localhost:8000/health"

# Run full pipeline (fetch + process with all personalities)
curl -X POST "http://localhost:8000/pipeline/Alberta?limit=5"
```

### ☁️ Serverless Usage

Use the serverless script to interact with your RunPod deployment:

#### Setup Environment

**Option 1: Use existing .env file (Recommended)**

Your `.env` file should already contain the RunPod configuration from deployment:
```bash
RUNPOD_API_KEY=rpa_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ENDPOINT_URL=https://api.runpod.ai/v2/your-endpoint-id/runsync
```

**Option 2: Add/Update RunPod credentials manually**
```bash
# Add to your .env file
echo "RUNPOD_API_KEY=your-runpod-api-key" >> .env
echo "ENDPOINT_URL=https://api.runpod.ai/v2/your-endpoint-id/runsync" >> .env

# Or export environment variables manually
export RUNPOD_API_KEY="your-runpod-api-key"
export ENDPOINT_URL="https://api.runpod.ai/v2/your-endpoint-id/runsync"
```

**Make script executable:**
```bash
chmod +x news_gather_serverless.sh
```

**Note:** The script automatically loads credentials from `.env` file if present, using `ENDPOINT_URL` and `RUNPOD_API_KEY` variables.

#### Basic Usage
```bash
# Fetch news for Alberta and save locally
./news_gather_serverless.sh --province "Alberta" --save-to-local

# Fetch 5 articles for Ontario and save to database
./news_gather_serverless.sh --province "Ontario" --save-to-db --limit 5

# Fetch without content scraping
./news_gather_serverless.sh --province "British Columbia" --no-scrape

# Save response to file
./news_gather_serverless.sh --province "Quebec" --output quebec_news.json
```

#### Advanced Options
```bash
# Verbose output with custom timeout
./news_gather_serverless.sh --province "Manitoba" \
    --save-to-local \
    --limit 15 \
    --verbose \
    --timeout 600

# Override endpoint and API key
./news_gather_serverless.sh --province "Saskatchewan" \
    --endpoint "https://custom-endpoint.com/runsync" \
    --api-key "custom-api-key" \
    --save-to-local

# Get help
./news_gather_serverless.sh --help
```

#### Testing
```bash
# Test the serverless script and local server
chmod +x test_serverless.sh
./test_serverless.sh
```

## API Endpoints

### News Collection
- `GET /news/{province}` - Get news for a province with optional save parameters
  - Query params: `limit`, `scrape`, `save_to_db`, `save_to_local`
- `POST /news` - Get news (POST body)
- `GET /provinces` - List all provinces

### AI Processing
- `POST /process` - Process articles with AI personality
- `GET /process/{province}/{host_type}` - Fetch and process latest news

### Web Scraping
- `POST /scrape` - Scrape specific URLs

### Pipeline
- `POST /pipeline/{province}` - Run complete news processing pipeline

### Database (if Supabase configured)
- `GET /sessions/{province}/latest` - Get latest session for province
- `GET /sessions/{session_id}/articles` - Get articles for session
- `GET /provinces/with-data` - Get provinces with data

### Local Storage
- `GET /local/sessions` - List all locally saved sessions
- `GET /local/sessions/{province}/latest` - Get latest local session for province
- `DELETE /local/sessions/old` - Delete old local sessions

## Project Structure

```
tkr-news-gather/
├── src/
│   ├── news/
│   │   ├── google_news_client.py    # Google News API integration
│   │   ├── article_scraper.py       # Web scraping with Crawl4ai
│   │   ├── news_processor.py        # AI processing with personalities
│   │   └── provinces.py             # Canadian province data
│   ├── utils/
│   │   ├── config.py                # Configuration management
│   │   ├── logger.py                # Logging utilities
│   │   ├── anthropic_client.py      # Claude AI client
│   │   └── supabase_client.py       # Database client
│   ├── api.py                       # Core API logic
│   └── main.py                      # FastAPI application
├── database/
│   └── schema.sql                   # Supabase database schema
├── tests/                           # Test files
├── news_data/                       # Local storage directory (created at runtime)
├── Dockerfile                       # Docker configuration
├── docker-compose.yml              # Docker Compose setup
├── runpod_handler.py               # RunPod serverless handler
├── start_server.sh                 # Local server startup script
├── news_gather_serverless.sh       # Serverless client script
├── test_serverless.sh              # Testing script
└── requirements.txt                # Python dependencies
```

## RunPod Deployment

### 🚀 Automated Deployment (Recommended)

Use the interactive deployment script for complete automated setup:

```bash
# Run the interactive deployment wizard
make deploy-runpod

# Or run directly
python3 deploy.py
```

The script will:
- ✅ Build and push Docker image automatically
- ✅ Generate all security credentials (JWT, API keys)
- ✅ Create RunPod template and endpoint via API
- ✅ Test the deployed endpoint
- ✅ Generate complete documentation

### 📋 Manual Deployment

For manual deployment on RunPod:

1. **Build Docker Image**:
```bash
docker build -t tkr-news-gather .
```

2. **Push to Registry** (Docker Hub, etc.)

3. **Deploy on RunPod**:
   - Use the `runpod_handler.py` as the entry point
   - Set environment variables in RunPod dashboard
   - Configure endpoints as needed

### RunPod Handler Usage

```python
# Example RunPod request
{
    "input": {
        "action": "get_news",
        "province": "Alberta", 
        "limit": 10,
        "scrape": true
    }
}
```

## Database Setup

### For New Projects (Recommended)

1. Create a new Supabase project at [supabase.com](https://supabase.com)
2. Run the complete schema with authentication:
   ```sql
   -- Copy and paste the content of database/schema_with_auth.sql
   -- into your Supabase SQL editor
   ```
3. Set environment variables in `.env`
4. The API will have full authentication and database functionality

### For Existing Projects

If you already have the basic schema from `database/schema.sql`:

1. Apply the authentication migration:
   ```sql
   -- Copy and paste the content of database/auth_migration.sql
   -- into your Supabase SQL editor
   ```
2. Update environment variables to include authentication settings

### Database Schema Options

| File | Purpose | Use Case |
|------|---------|----------|
| `schema.sql` | Original news tables only | Legacy/basic setup |
| `auth_migration.sql` | Adds authentication to existing setup | Upgrading existing projects |
| `schema_with_auth.sql` | Complete schema with authentication | **New projects (recommended)** |

### Authentication Setup

After running the schema, you can:
- Register users via `/auth/register`
- Authenticate via `/auth/login` 
- Access protected endpoints with JWT tokens
- Use role-based permissions (user/editor/admin)

## Testing

```bash
# Run local tests
python run_local.py

# Test RunPod handler
python runpod_handler.py

# Test specific components
python -m pytest tests/
```

## Configuration

All configuration is managed through environment variables. See `.env.example` for all available options.

### Key Settings
- `ANTHROPIC_API_KEY`: Required for AI processing
- `DEFAULT_NEWS_LIMIT`: Default number of articles to fetch (10)
- `SCRAPE_TIMEOUT`: Web scraping timeout in seconds (30)
- `LOG_LEVEL`: Logging level (INFO)

## Development

### Adding New Provinces
Edit `src/news/provinces.py` to add or modify province configurations.

### Adding New Host Personalities
Modify `src/news/news_processor.py` to add new AI personalities.

### Extending API
Add new endpoints in `src/main.py` following FastAPI patterns.

## Troubleshooting

### Common Issues

1. **Missing API Key**: Ensure `ANTHROPIC_API_KEY` is set
2. **Scraping Failures**: Some sites may block automated scraping
3. **Database Connection**: Check Supabase credentials if using database
4. **Rate Limits**: Respect Google News and Anthropic API rate limits

### Logs

Set `LOG_LEVEL=DEBUG` for detailed logging information.

## License

[Add your license information here]

## Support

For issues and feature requests, please [create an issue](link-to-issues) in the repository.