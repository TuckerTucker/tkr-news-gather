#!/bin/bash
# Security scanning script for local development
# Updated: 2025-01-04

set -e

echo "🔍 TKR News Gatherer Security Scan"
echo "=================================="

# Create reports directory
mkdir -p reports/security

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if security tools are installed
check_tools() {
    print_status "Checking security tools..."
    
    tools=("safety" "bandit" "pip-audit" "semgrep")
    missing_tools=()
    
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        print_error "Missing tools: ${missing_tools[*]}"
        print_status "Installing missing tools..."
        pip install -r requirements-security.txt
    else
        print_success "All security tools are available"
    fi
}

# Run dependency vulnerability scan
scan_dependencies() {
    print_status "Scanning dependencies for vulnerabilities..."
    
    echo "Running Safety scan..."
    if safety check --json --output reports/security/safety-report.json; then
        print_success "Safety scan completed - no vulnerabilities found"
    else
        print_warning "Safety scan found potential issues - check reports/security/safety-report.json"
    fi
    
    echo "Running pip-audit scan..."
    if pip-audit --format=json --output=reports/security/pip-audit-report.json --desc; then
        print_success "pip-audit scan completed - no vulnerabilities found"
    else
        print_warning "pip-audit found potential issues - check reports/security/pip-audit-report.json"
    fi
}

# Run static code analysis
scan_code() {
    print_status "Running static code analysis..."
    
    echo "Running Bandit security linter..."
    if bandit -r src/ -f json -o reports/security/bandit-report.json; then
        print_success "Bandit scan completed - no security issues found"
    else
        print_warning "Bandit found potential security issues - check reports/security/bandit-report.json"
        bandit -r src/ -ll
    fi
    
    echo "Running Semgrep analysis..."
    if semgrep --config=auto src/ --json --output=reports/security/semgrep-report.json; then
        print_success "Semgrep scan completed - no issues found"
    else
        print_warning "Semgrep found potential issues - check reports/security/semgrep-report.json"
    fi
}

# Generate Software Bill of Materials
generate_sbom() {
    print_status "Generating Software Bill of Materials (SBOM)..."
    
    if cyclonedx-py requirements -o reports/security/sbom.json; then
        print_success "SBOM generated successfully"
    else
        print_error "Failed to generate SBOM"
    fi
}

# Check license compliance
check_licenses() {
    print_status "Checking license compliance..."
    
    if pip-licenses --format=json --output-file=reports/security/licenses.json; then
        print_success "License report generated"
        pip-licenses --format=markdown --output-file=reports/security/licenses.md
        
        # Check for problematic licenses
        if grep -q "GPL\|AGPL\|LGPL" reports/security/licenses.md; then
            print_warning "Found copyleft licenses - review for compliance"
        else
            print_success "All licenses are permissive"
        fi
    else
        print_error "Failed to generate license report"
    fi
}

# Scan Docker image if it exists
scan_docker() {
    if docker images | grep -q "tkr-news-gather"; then
        print_status "Scanning Docker image..."
        
        # Install trivy if not available
        if ! command -v trivy &> /dev/null; then
            print_status "Installing Trivy..."
            curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
        fi
        
        if trivy image --format json --output reports/security/trivy-report.json tkr-news-gather:latest; then
            print_success "Docker image scan completed"
        else
            print_warning "Docker image scan found issues - check reports/security/trivy-report.json"
        fi
    else
        print_status "No Docker image found - skipping container scan"
    fi
}

# Generate summary report
generate_summary() {
    print_status "Generating security summary..."
    
    cat > reports/security/summary.md << EOF
# Security Scan Summary

**Scan Date:** $(date)
**Repository:** TKR News Gatherer

## Scans Performed

- ✅ Dependency vulnerability scan (Safety + pip-audit)
- ✅ Static code analysis (Bandit + Semgrep)
- ✅ Software Bill of Materials (SBOM)
- ✅ License compliance check
$(if docker images | grep -q "tkr-news-gather"; then echo "- ✅ Container security scan (Trivy)"; else echo "- ⏭️ Container security scan (no image found)"; fi)

## Report Files

- \`safety-report.json\` - Dependency vulnerabilities
- \`pip-audit-report.json\` - PyPA security audit
- \`bandit-report.json\` - Python security issues
- \`semgrep-report.json\` - Advanced static analysis
- \`sbom.json\` - Software Bill of Materials
- \`licenses.json/md\` - License compliance
$(if docker images | grep -q "tkr-news-gather"; then echo "- \`trivy-report.json\` - Container vulnerabilities"; fi)

## Next Steps

1. Review all JSON reports for detailed findings
2. Address any HIGH or CRITICAL severity issues
3. Update dependencies with security patches
4. Implement security fixes in code
5. Re-run scans to verify fixes

EOF

    print_success "Security summary generated at reports/security/summary.md"
}

# Main execution
main() {
    check_tools
    scan_dependencies
    scan_code
    generate_sbom
    check_licenses
    scan_docker
    generate_summary
    
    echo ""
    print_success "Security scan completed! Check reports/security/ for detailed results."
    echo "📊 Summary report: reports/security/summary.md"
}

# Run main function
main "$@"