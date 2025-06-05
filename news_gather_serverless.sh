#!/bin/bash

# TKR News Gather Serverless Client
# Usage: ./news_gather_serverless.sh --province "Alberta" [--save-to-local | --save-to-db] [options]

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
fi

# Default values - use ENDPOINT_URL from .env if available, fallback to constructed URL using ENDPOINT_ID
if [ -z "$ENDPOINT_URL" ] && [ -z "$RUNPOD_ENDPOINT_URL" ]; then
    if [ -n "$ENDPOINT_ID" ]; then
        ENDPOINT_URL="https://api.runpod.ai/v2/${ENDPOINT_ID}/runsync"
    else
        ENDPOINT_URL="https://api.runpod.ai/v2/your-endpoint-id/runsync"
    fi
else
    ENDPOINT_URL="${ENDPOINT_URL:-$RUNPOD_ENDPOINT_URL}"
fi
API_KEY="${RUNPOD_API_KEY:-}"
PROVINCE=""
SAVE_TO_LOCAL=false
SAVE_TO_DB=false
LIMIT=10
SCRAPE=true
VERBOSE=false
OUTPUT_FILE=""
TIMEOUT=300  # 5 minutes default

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    cat << EOF
Usage: $0 --province PROVINCE [OPTIONS]

Interact with TKR News Gather serverless endpoint to fetch and save news.

REQUIRED:
    --province PROVINCE     Canadian province name (e.g., "Alberta", "Ontario")

OPTIONS:
    --save-to-local        Save results to local filesystem
    --save-to-db          Save results to Supabase database
    --limit NUMBER        Number of articles to fetch (default: 10)
    --no-scrape          Skip article content scraping
    --endpoint URL        Override default RunPod endpoint URL
    --api-key KEY        RunPod API key (or set RUNPOD_API_KEY env var)
    --output FILE        Save response to file
    --timeout SECONDS    Request timeout in seconds (default: 300)
    --verbose            Show detailed output
    --help               Show this help message

EXAMPLES:
    # Fetch news for Alberta and save locally
    $0 --province "Alberta" --save-to-local

    # Fetch 5 articles for Ontario and save to database
    $0 --province "Ontario" --save-to-db --limit 5

    # Fetch news without scraping content
    $0 --province "British Columbia" --no-scrape

    # Save response to file
    $0 --province "Quebec" --output quebec_news.json

ENVIRONMENT VARIABLES:
    ENDPOINT_URL         RunPod endpoint URL (from .env)
    ENDPOINT_ID          RunPod endpoint ID (used to construct URL if ENDPOINT_URL not set)
    RUNPOD_ENDPOINT_URL  Alternative endpoint URL variable
    RUNPOD_API_KEY       RunPod API key
    
NOTE: The script automatically loads environment variables from .env file if present.
      Priority: ENDPOINT_URL > RUNPOD_ENDPOINT_URL > constructed from ENDPOINT_ID
EOF
}

# Function to log messages
log() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" >&2
    fi
}

# Function to show error
error() {
    echo -e "${RED}Error:${NC} $1" >&2
}

# Function to show success
success() {
    echo -e "${GREEN}Success:${NC} $1"
}

# Function to show warning
warning() {
    echo -e "${YELLOW}Warning:${NC} $1"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --province)
            PROVINCE="$2"
            shift 2
            ;;
        --save-to-local)
            SAVE_TO_LOCAL=true
            shift
            ;;
        --save-to-db)
            SAVE_TO_DB=true
            shift
            ;;
        --limit)
            LIMIT="$2"
            shift 2
            ;;
        --no-scrape)
            SCRAPE=false
            shift
            ;;
        --endpoint)
            ENDPOINT_URL="$2"
            shift 2
            ;;
        --api-key)
            API_KEY="$2"
            shift 2
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate required arguments
if [ -z "$PROVINCE" ]; then
    error "Province is required"
    usage
    exit 1
fi

# Check for API key
if [ -z "$API_KEY" ]; then
    error "RunPod API key not provided. Set RUNPOD_API_KEY environment variable or use --api-key"
    if [ -f ".env" ]; then
        warning "Found .env file but RUNPOD_API_KEY is not set or empty"
    fi
    exit 1
fi

# Show loaded configuration if verbose
if [ "$VERBOSE" = true ]; then
    log "Configuration loaded:"
    log "  Endpoint URL: $ENDPOINT_URL"
    log "  API Key: ${API_KEY:0:20}..." # Show only first 20 characters for security
fi

# Always show the URL being used for transparency
echo "🌐 Using endpoint: $ENDPOINT_URL"

# Validate province name (basic check)
VALID_PROVINCES=("Alberta" "British Columbia" "Manitoba" "New Brunswick" "Newfoundland and Labrador" "Northwest Territories" "Nova Scotia" "Nunavut" "Ontario" "Prince Edward Island" "Quebec" "Saskatchewan" "Yukon")
PROVINCE_VALID=false
for valid_province in "${VALID_PROVINCES[@]}"; do
    # Convert to lowercase using tr for better compatibility
    if [[ "$(echo "$valid_province" | tr '[:upper:]' '[:lower:]')" == "$(echo "$PROVINCE" | tr '[:upper:]' '[:lower:]')" ]]; then
        PROVINCE_VALID=true
        break
    fi
done

if [ "$PROVINCE_VALID" = false ]; then
    warning "Province '$PROVINCE' may not be recognized. Valid provinces are:"
    printf '%s\n' "${VALID_PROVINCES[@]}"
fi

# Build the request payload
log "Building request payload..."
PAYLOAD=$(cat <<EOF
{
    "input": {
        "action": "get_news",
        "province": "$PROVINCE",
        "limit": $LIMIT,
        "scrape": $SCRAPE,
        "save_to_db": $SAVE_TO_DB,
        "save_to_local": $SAVE_TO_LOCAL
    }
}
EOF
)

log "Request payload: $PAYLOAD"

# Display request summary
echo "📰 TKR News Gather Request Summary:"
echo "  Province: $PROVINCE"
echo "  Articles: $LIMIT"
echo "  Scrape: $SCRAPE"
echo "  Save to Local: $SAVE_TO_LOCAL"
echo "  Save to DB: $SAVE_TO_DB"
echo "  Endpoint: $(echo $ENDPOINT_URL | sed 's|/runsync$||' | sed 's|.*v2/||')"
echo ""

# Make the API request
log "Sending request to $ENDPOINT_URL"
echo "🔄 Fetching news..."

RESPONSE=$(curl -s -w "\n%{http_code}" \
    --max-time "$TIMEOUT" \
    -X POST \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    "$ENDPOINT_URL")

# Extract HTTP status code
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')

log "HTTP Status Code: $HTTP_CODE"
log "Response body: $RESPONSE_BODY"

# Check HTTP status
if [ "$HTTP_CODE" -ne 200 ]; then
    error "Request failed with HTTP status $HTTP_CODE"
    if [ -n "$RESPONSE_BODY" ]; then
        echo "Response: $RESPONSE_BODY" >&2
    fi
    exit 1
fi

# Parse the response
if ! echo "$RESPONSE_BODY" | jq empty 2>/dev/null; then
    error "Invalid JSON response"
    echo "Response: $RESPONSE_BODY" >&2
    exit 1
fi

# Check for RunPod status
RUNPOD_STATUS=$(echo "$RESPONSE_BODY" | jq -r '.status // empty')
if [ "$RUNPOD_STATUS" = "IN_QUEUE" ] || [ "$RUNPOD_STATUS" = "IN_PROGRESS" ]; then
    warning "Job is still in progress. Status: $RUNPOD_STATUS"
    echo "Job ID: $(echo "$RESPONSE_BODY" | jq -r '.id // empty')"
    echo "Use RunPod's status endpoint to check progress."
    exit 0
fi

# Extract the actual result from RunPod response
RESULT=$(echo "$RESPONSE_BODY" | jq '.output // empty')
if [ -z "$RESULT" ] || [ "$RESULT" = "null" ]; then
    error "No output in response"
    echo "Full response: $RESPONSE_BODY" >&2
    exit 1
fi

# Check API response status
API_STATUS=$(echo "$RESULT" | jq -r '.status // empty')
if [ "$API_STATUS" != "success" ]; then
    error "API returned error status: $API_STATUS"
    ERROR_MSG=$(echo "$RESULT" | jq -r '.error // empty')
    if [ -n "$ERROR_MSG" ] && [ "$ERROR_MSG" != "null" ]; then
        echo "Error message: $ERROR_MSG" >&2
    fi
    exit 1
fi

# Extract results
TOTAL_RESULTS=$(echo "$RESULT" | jq -r '.totalResults // 0')
ARTICLES=$(echo "$RESULT" | jq '.results // []')

# Display results summary
echo ""
success "Fetched $TOTAL_RESULTS articles for $PROVINCE"

# Handle local saving on user's machine
if [ "$SAVE_TO_LOCAL" = true ]; then
    SAVE_REQUESTED=$(echo "$RESULT" | jq -r '.metadata.save_to_local_requested // false')
    if [ "$SAVE_REQUESTED" = "true" ]; then
        # Create local news_data directory if it doesn't exist
        mkdir -p news_data/"$(echo "$PROVINCE" | tr '[:upper:]' '[:lower:]')"
        
        # Generate filename with timestamp
        TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
        LOCAL_FILENAME="news_data/$(echo "$PROVINCE" | tr '[:upper:]' '[:lower:]')/${PROVINCE}_${TIMESTAMP}.json"
        
        # Save the result to local file
        echo "$RESULT" | jq '.' > "$LOCAL_FILENAME"
        
        if [ $? -eq 0 ]; then
            success "Saved to local filesystem: $LOCAL_FILENAME"
        else
            warning "Failed to save to local filesystem"
        fi
    else
        warning "Local save was requested but not processed by server"
    fi
fi

if [ "$SAVE_TO_DB" = true ]; then
    SESSION_ID=$(echo "$RESULT" | jq -r '.metadata.session_id // empty')
    if [ -n "$SESSION_ID" ] && [ "$SESSION_ID" != "null" ]; then
        success "Saved to database with session ID: $SESSION_ID"
    else
        warning "Database save was requested but no session ID returned"
    fi
fi

# Display article summaries
if [ "$TOTAL_RESULTS" -gt 0 ]; then
    echo ""
    echo "📄 Article Summaries:"
    echo "$ARTICLES" | jq -r '.[] | "  • \(.title) (\(.source_name))"' | head -10
    
    if [ "$TOTAL_RESULTS" -gt 10 ]; then
        echo "  ... and $((TOTAL_RESULTS - 10)) more articles"
    fi
fi

# Save to output file if requested
if [ -n "$OUTPUT_FILE" ]; then
    echo "$RESULT" | jq '.' > "$OUTPUT_FILE"
    success "Full response saved to: $OUTPUT_FILE"
fi

# Show sample article if verbose
if [ "$VERBOSE" = true ] && [ "$TOTAL_RESULTS" -gt 0 ]; then
    echo ""
    echo "Sample article details:"
    echo "$ARTICLES" | jq '.[0]' | jq '{title, link, source_name, pub_date, summary: (.summary | if length > 200 then .[0:200] + "..." else . end)}'
fi