#!/bin/bash
# Dependency Security and Health Check Script
# Comprehensive dependency analysis and security scanning

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REPORTS_DIR="$PROJECT_ROOT/security-reports"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create reports directory
mkdir -p "$REPORTS_DIR"

echo -e "${BLUE}🔍 TKR News Gather - Dependency Security Check${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if Poetry is available
if command -v poetry &> /dev/null; then
    PACKAGE_MANAGER="poetry"
    echo -e "${GREEN}✅ Using Poetry for dependency management${NC}"
else
    PACKAGE_MANAGER="pip"
    echo -e "${YELLOW}⚠️  Poetry not found, using pip${NC}"
fi

# Function to run command and capture output
run_check() {
    local name="$1"
    local command="$2"
    local output_file="$3"
    local continue_on_error="${4:-true}"
    
    echo -e "${BLUE}🔧 Running $name...${NC}"
    
    if [[ "$continue_on_error" == "true" ]]; then
        if eval "$command" > "$output_file" 2>&1; then
            echo -e "${GREEN}✅ $name completed successfully${NC}"
        else
            echo -e "${YELLOW}⚠️  $name completed with warnings${NC}"
        fi
    else
        if eval "$command" > "$output_file" 2>&1; then
            echo -e "${GREEN}✅ $name completed successfully${NC}"
        else
            echo -e "${RED}❌ $name failed${NC}"
            return 1
        fi
    fi
    echo ""
}

# 1. Dependency vulnerability scanning
echo -e "${BLUE}1️⃣ Dependency Vulnerability Scanning${NC}"
echo "-----------------------------------"

# pip-audit (works with both pip and poetry)
if command -v pip-audit &> /dev/null; then
    run_check "pip-audit vulnerability scan" \
        "pip-audit --desc --format=json" \
        "$REPORTS_DIR/pip-audit-report.json"
    
    run_check "pip-audit human-readable report" \
        "pip-audit --desc" \
        "$REPORTS_DIR/pip-audit-report.txt"
else
    echo -e "${YELLOW}⚠️  pip-audit not found. Install with: pip install pip-audit${NC}"
fi

# Safety check
if command -v safety &> /dev/null; then
    run_check "Safety vulnerability database check" \
        "safety check --json" \
        "$REPORTS_DIR/safety-report.json"
    
    run_check "Safety human-readable report" \
        "safety check" \
        "$REPORTS_DIR/safety-report.txt"
else
    echo -e "${YELLOW}⚠️  Safety not found. Install with: pip install safety${NC}"
fi

# 2. Code security analysis
echo -e "${BLUE}2️⃣ Code Security Analysis${NC}"
echo "-------------------------"

# Bandit security linter
if command -v bandit &> /dev/null; then
    run_check "Bandit security analysis" \
        "bandit -r src/ -f json" \
        "$REPORTS_DIR/bandit-report.json"
    
    run_check "Bandit human-readable report" \
        "bandit -r src/ --skip B101,B601" \
        "$REPORTS_DIR/bandit-report.txt"
else
    echo -e "${YELLOW}⚠️  Bandit not found. Install with: pip install bandit${NC}"
fi

# Semgrep (if available)
if command -v semgrep &> /dev/null; then
    run_check "Semgrep security patterns" \
        "semgrep --config=p/security-audit --config=p/secrets --config=p/python --json ." \
        "$REPORTS_DIR/semgrep-report.json"
else
    echo -e "${YELLOW}⚠️  Semgrep not found. Install with: pip install semgrep${NC}"
fi

# 3. Dependency health analysis
echo -e "${BLUE}3️⃣ Dependency Health Analysis${NC}"
echo "-----------------------------"

# Poetry dependency analysis
if [[ "$PACKAGE_MANAGER" == "poetry" ]]; then
    run_check "Poetry dependency tree" \
        "poetry show --tree" \
        "$REPORTS_DIR/dependency-tree.txt"
    
    run_check "Poetry outdated packages" \
        "poetry show --outdated" \
        "$REPORTS_DIR/outdated-packages.txt"
else
    # pip-based analysis
    run_check "pip dependency list" \
        "pip list --format=json" \
        "$REPORTS_DIR/pip-list.json"
    
    if command -v pip-check &> /dev/null; then
        run_check "pip dependency conflicts" \
            "pip-check" \
            "$REPORTS_DIR/pip-conflicts.txt"
    fi
fi

# 4. License compliance check
echo -e "${BLUE}4️⃣ License Compliance Check${NC}"
echo "---------------------------"

if command -v pip-licenses &> /dev/null; then
    run_check "License analysis (JSON)" \
        "pip-licenses --format=json" \
        "$REPORTS_DIR/licenses.json"
    
    run_check "License analysis (Markdown)" \
        "pip-licenses --format=markdown" \
        "$REPORTS_DIR/LICENSES.md"
    
    # Check for GPL licenses
    echo -e "${BLUE}🔧 Checking for GPL licenses...${NC}"
    if pip-licenses | grep -i gpl > "$REPORTS_DIR/gpl-check.txt" 2>&1; then
        echo -e "${YELLOW}⚠️  GPL licenses found - review for commercial compatibility${NC}"
    else
        echo -e "${GREEN}✅ No GPL licenses found${NC}"
        echo "No GPL licenses found" > "$REPORTS_DIR/gpl-check.txt"
    fi
else
    echo -e "${YELLOW}⚠️  pip-licenses not found. Install with: pip install pip-licenses${NC}"
fi

# 5. SBOM Generation
echo -e "${BLUE}5️⃣ Software Bill of Materials (SBOM)${NC}"
echo "-----------------------------------"

if command -v cyclonedx-py &> /dev/null; then
    run_check "SBOM generation (CycloneDX format)" \
        "cyclonedx-py --output-format=json --output-file=$REPORTS_DIR/sbom.json ." \
        "$REPORTS_DIR/sbom-generation.log"
else
    echo -e "${YELLOW}⚠️  cyclonedx-py not found. Install with: pip install cyclonedx-bom${NC}"
fi

# 6. Docker security (if Dockerfile exists)
if [[ -f "$PROJECT_ROOT/Dockerfile" ]]; then
    echo -e "${BLUE}6️⃣ Container Security${NC}"
    echo "-------------------"
    
    if command -v docker &> /dev/null; then
        # Build image for scanning
        echo -e "${BLUE}🔧 Building Docker image...${NC}"
        docker build -t tkr-news-gather:security-scan "$PROJECT_ROOT" > "$REPORTS_DIR/docker-build.log" 2>&1
        
        # Trivy scan (if available)
        if command -v trivy &> /dev/null; then
            run_check "Trivy container vulnerability scan" \
                "trivy image --format json tkr-news-gather:security-scan" \
                "$REPORTS_DIR/trivy-report.json"
        else
            echo -e "${YELLOW}⚠️  Trivy not found. Install from https://trivy.dev${NC}"
        fi
        
        # Cleanup
        docker rmi tkr-news-gather:security-scan > /dev/null 2>&1 || true
    else
        echo -e "${YELLOW}⚠️  Docker not found - skipping container security scan${NC}"
    fi
fi

# 7. Generate comprehensive report
echo -e "${BLUE}7️⃣ Generating Security Summary${NC}"
echo "-----------------------------"

SUMMARY_FILE="$REPORTS_DIR/security-summary.md"

cat > "$SUMMARY_FILE" << EOF
# TKR News Gather - Security Analysis Summary

**Date:** $(date)
**Scan Type:** Local dependency and security analysis
**Project:** tkr-news-gather

## Executive Summary

This report provides a comprehensive analysis of dependency security, code vulnerabilities, and license compliance for the TKR News Gather project.

## Scan Results

### 1. Dependency Vulnerabilities

EOF

# Add results based on what was actually run
if [[ -f "$REPORTS_DIR/pip-audit-report.json" ]]; then
    echo "✅ **pip-audit**: Completed - see \`pip-audit-report.json\`" >> "$SUMMARY_FILE"
else
    echo "❌ **pip-audit**: Not available" >> "$SUMMARY_FILE"
fi

if [[ -f "$REPORTS_DIR/safety-report.json" ]]; then
    echo "✅ **Safety**: Completed - see \`safety-report.json\`" >> "$SUMMARY_FILE"
else
    echo "❌ **Safety**: Not available" >> "$SUMMARY_FILE"
fi

cat >> "$SUMMARY_FILE" << EOF

### 2. Code Security Analysis

EOF

if [[ -f "$REPORTS_DIR/bandit-report.json" ]]; then
    echo "✅ **Bandit**: Completed - see \`bandit-report.json\`" >> "$SUMMARY_FILE"
else
    echo "❌ **Bandit**: Not available" >> "$SUMMARY_FILE"
fi

if [[ -f "$REPORTS_DIR/semgrep-report.json" ]]; then
    echo "✅ **Semgrep**: Completed - see \`semgrep-report.json\`" >> "$SUMMARY_FILE"
else
    echo "❌ **Semgrep**: Not available" >> "$SUMMARY_FILE"
fi

cat >> "$SUMMARY_FILE" << EOF

### 3. License Compliance

EOF

if [[ -f "$REPORTS_DIR/licenses.json" ]]; then
    echo "✅ **License Analysis**: Completed - see \`licenses.json\` and \`LICENSES.md\`" >> "$SUMMARY_FILE"
else
    echo "❌ **License Analysis**: Not available" >> "$SUMMARY_FILE"
fi

cat >> "$SUMMARY_FILE" << EOF

### 4. Supply Chain Security

EOF

if [[ -f "$REPORTS_DIR/sbom.json" ]]; then
    echo "✅ **SBOM**: Generated - see \`sbom.json\`" >> "$SUMMARY_FILE"
else
    echo "❌ **SBOM**: Not generated" >> "$SUMMARY_FILE"
fi

cat >> "$SUMMARY_FILE" << EOF

## Next Steps

1. Review all JSON reports for detailed findings
2. Address any high-severity vulnerabilities immediately
3. Plan updates for outdated dependencies
4. Ensure license compliance for commercial use
5. Integrate findings into development workflow

## Report Files

All detailed reports are available in the \`security-reports/\` directory:

- \`pip-audit-report.json\` - Known vulnerability database check
- \`safety-report.json\` - Python-specific security database
- \`bandit-report.json\` - Static code security analysis
- \`licenses.json\` - Complete license analysis
- \`sbom.json\` - Software Bill of Materials
- \`security-summary.md\` - This summary report

For human-readable versions, see the corresponding \`.txt\` files.

EOF

echo -e "${GREEN}📊 Security summary generated: $SUMMARY_FILE${NC}"
echo ""

# Final summary
echo -e "${BLUE}🎉 Dependency Security Check Complete!${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""
echo -e "${GREEN}📁 All reports saved to: $REPORTS_DIR${NC}"
echo -e "${GREEN}📄 Summary report: $SUMMARY_FILE${NC}"
echo ""
echo -e "${YELLOW}⚡ Quick Actions:${NC}"
echo "1. Review the summary: cat $SUMMARY_FILE"
echo "2. Check vulnerabilities: cat $REPORTS_DIR/pip-audit-report.txt"
echo "3. Review licenses: cat $REPORTS_DIR/LICENSES.md"
echo ""
echo -e "${BLUE}💡 Tip: Set up automated scanning in CI/CD with the provided GitHub Actions workflow${NC}"