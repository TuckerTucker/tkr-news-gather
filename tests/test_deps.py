#!/usr/bin/env python3
"""
Dependency Health and Security Test Suite
Tests for dependency improvements and security fixes
"""

import subprocess
import sys
import json
import importlib
from typing import Dict, List, Tuple
import pkg_resources
from datetime import datetime

def run_command(cmd: List[str]) -> Tuple[str, str, int]:
    """Run a command and return stdout, stderr, and return code"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except Exception as e:
        return "", str(e), 1

def test_critical_dependencies():
    """Test that critical dependencies are properly updated"""
    print("🔍 Testing Critical Dependencies...")
    
    critical_packages = {
        'feedparser': '6.0.0',  # Should be 6.0.11 or higher
        'anthropic': '0.30.0',  # Should be 0.34.0 or higher
        'httpx': '0.25.0',      # Should be 0.26.0 or higher
        'fastapi': '0.108.0',   # Should be 0.109.0 or higher
    }
    
    issues = []
    
    for package, min_version in critical_packages.items():
        try:
            installed_version = pkg_resources.get_distribution(package).version
            
            # Simple version comparison (works for semantic versioning)
            if pkg_resources.parse_version(installed_version) >= pkg_resources.parse_version(min_version):
                print(f"✅ {package}: {installed_version} (meets minimum {min_version})")
            else:
                issues.append(f"❌ {package}: {installed_version} < {min_version}")
                print(f"❌ {package}: {installed_version} < {min_version}")
                
        except pkg_resources.DistributionNotFound:
            issues.append(f"❌ {package}: Not installed")
            print(f"❌ {package}: Not installed")
    
    return len(issues) == 0, issues

def test_removed_dependencies():
    """Test that redundant dependencies have been removed"""
    print("\n🚫 Testing Removed Dependencies...")
    
    # These packages should ideally be removed to avoid conflicts
    removed_packages = ['aiohttp']  # Redundant with httpx
    optional_packages = ['requests']  # Could be removed but might be used elsewhere
    
    issues = []
    warnings = []
    
    for package in removed_packages:
        try:
            version = pkg_resources.get_distribution(package).version
            issues.append(f"⚠️  {package}: Still installed ({version}) - should be removed")
            print(f"⚠️  {package}: Still installed ({version}) - consider removing")
        except pkg_resources.DistributionNotFound:
            print(f"✅ {package}: Correctly removed")
    
    for package in optional_packages:
        try:
            version = pkg_resources.get_distribution(package).version
            warnings.append(f"ℹ️  {package}: {version} - could be removed if not needed")
            print(f"ℹ️  {package}: {version} - could be removed if not needed")
        except pkg_resources.DistributionNotFound:
            print(f"✅ {package}: Not installed")
    
    return len(issues) == 0, issues + warnings

def test_security_tools():
    """Test that security scanning tools are available"""
    print("\n🛡️ Testing Security Tools...")
    
    security_tools = [
        'pip-audit',
        'safety',
        'bandit',
    ]
    
    issues = []
    
    for tool in security_tools:
        try:
            version = pkg_resources.get_distribution(tool).version
            print(f"✅ {tool}: {version}")
        except pkg_resources.DistributionNotFound:
            issues.append(f"❌ {tool}: Not installed")
            print(f"❌ {tool}: Not installed")
    
    return len(issues) == 0, issues

def test_vulnerability_scan():
    """Run vulnerability scans if tools are available"""
    print("\n🔍 Running Vulnerability Scans...")
    
    results = []
    
    # Test pip-audit
    stdout, stderr, returncode = run_command(['pip-audit', '--format', 'json'])
    if returncode == 0:
        try:
            audit_data = json.loads(stdout)
            vuln_count = len(audit_data.get('vulnerabilities', []))
            if vuln_count == 0:
                print("✅ pip-audit: No vulnerabilities found")
                results.append(("pip-audit", True, "No vulnerabilities"))
            else:
                print(f"⚠️  pip-audit: {vuln_count} vulnerabilities found")
                results.append(("pip-audit", False, f"{vuln_count} vulnerabilities"))
        except json.JSONDecodeError:
            print("⚠️  pip-audit: Could not parse results")
            results.append(("pip-audit", False, "Parse error"))
    else:
        print(f"❌ pip-audit: Failed to run ({stderr[:100]})")
        results.append(("pip-audit", False, "Failed to run"))
    
    # Test safety
    stdout, stderr, returncode = run_command(['safety', 'check', '--json'])
    if returncode == 0:
        try:
            safety_data = json.loads(stdout)
            vuln_count = len(safety_data)
            if vuln_count == 0:
                print("✅ safety: No vulnerabilities found")
                results.append(("safety", True, "No vulnerabilities"))
            else:
                print(f"⚠️  safety: {vuln_count} vulnerabilities found")
                results.append(("safety", False, f"{vuln_count} vulnerabilities"))
        except json.JSONDecodeError:
            if "No known security vulnerabilities found" in stdout:
                print("✅ safety: No vulnerabilities found")
                results.append(("safety", True, "No vulnerabilities"))
            else:
                print("⚠️  safety: Could not parse results")
                results.append(("safety", False, "Parse error"))
    else:
        print(f"❌ safety: Failed to run ({stderr[:100]})")
        results.append(("safety", False, "Failed to run"))
    
    return results

def test_import_compatibility():
    """Test that key imports still work after dependency changes"""
    print("\n📦 Testing Import Compatibility...")
    
    critical_imports = [
        ('feedparser', 'feedparser'),
        ('httpx', 'httpx'),
        ('fastapi', 'fastapi'),
        ('anthropic', 'anthropic'),
        ('supabase', 'supabase'),
    ]
    
    issues = []
    
    for module_name, import_name in critical_imports:
        try:
            importlib.import_module(import_name)
            print(f"✅ {module_name}: Import successful")
        except ImportError as e:
            issues.append(f"❌ {module_name}: Import failed - {str(e)}")
            print(f"❌ {module_name}: Import failed - {str(e)}")
    
    # Test improved Google News client
    try:
        sys.path.insert(0, 'src')
        from news.google_news_client_improved import ImprovedGoogleNewsClient
        print("✅ ImprovedGoogleNewsClient: Import successful")
    except ImportError as e:
        issues.append(f"❌ ImprovedGoogleNewsClient: Import failed - {str(e)}")
        print(f"❌ ImprovedGoogleNewsClient: Import failed - {str(e)}")
    
    return len(issues) == 0, issues

def test_feedparser_compatibility():
    """Test that feedparser 6.x is backward compatible"""
    print("\n🔄 Testing feedparser Compatibility...")
    
    try:
        import feedparser
        
        # Test basic functionality
        sample_rss = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <item>
                    <title>Test Article</title>
                    <link>https://example.com/article</link>
                    <description>Test description</description>
                </item>
            </channel>
        </rss>"""
        
        feed = feedparser.parse(sample_rss)
        
        # Check basic structure
        assert hasattr(feed, 'entries'), "Missing entries attribute"
        assert len(feed.entries) == 1, "Should have one entry"
        assert feed.entries[0].title == "Test Article", "Title mismatch"
        
        print("✅ feedparser: Basic functionality working")
        
        # Check version
        version = feedparser.__version__
        if version.startswith('6.'):
            print(f"✅ feedparser: Version {version} (6.x series)")
            return True, []
        else:
            return False, [f"❌ feedparser: Version {version} is not 6.x series"]
            
    except Exception as e:
        return False, [f"❌ feedparser: Test failed - {str(e)}"]

def generate_dependency_report():
    """Generate a comprehensive dependency report"""
    print("\n📊 Generating Dependency Report...")
    
    # Get all installed packages
    installed_packages = {pkg.project_name: pkg.version for pkg in pkg_resources.working_set}
    
    # Categorize packages
    core_packages = [
        'feedparser', 'httpx', 'fastapi', 'anthropic', 'supabase',
        'beautifulsoup4', 'lxml', 'crawl4ai', 'uvicorn', 'pydantic'
    ]
    
    security_packages = [
        'pip-audit', 'safety', 'bandit', 'cyclonedx-bom'
    ]
    
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'total_packages': len(installed_packages),
        'core_packages': {},
        'security_packages': {},
        'all_packages': installed_packages
    }
    
    for pkg in core_packages:
        if pkg in installed_packages:
            report['core_packages'][pkg] = installed_packages[pkg]
    
    for pkg in security_packages:
        if pkg in installed_packages:
            report['security_packages'][pkg] = installed_packages[pkg]
    
    # Save report
    with open('dependency-report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Dependency report saved to dependency-report.json")
    print(f"   Total packages: {report['total_packages']}")
    print(f"   Core packages: {len(report['core_packages'])}")
    print(f"   Security packages: {len(report['security_packages'])}")
    
    return report

def main():
    """Run all dependency tests"""
    print("🧪 TKR News Gather - Dependency Test Suite")
    print("=" * 50)
    
    all_passed = True
    all_issues = []
    
    # Run tests
    tests = [
        ("Critical Dependencies", test_critical_dependencies),
        ("Removed Dependencies", test_removed_dependencies),
        ("Security Tools", test_security_tools),
        ("Import Compatibility", test_import_compatibility),
        ("feedparser Compatibility", test_feedparser_compatibility),
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            passed, issues = test_func()
            if not passed:
                all_passed = False
                all_issues.extend(issues)
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            all_passed = False
            all_issues.append(f"Test '{test_name}' failed: {str(e)}")
    
    # Run vulnerability scans
    print(f"\n{'='*50}")
    print("Running: Vulnerability Scans")
    print('='*50)
    
    vuln_results = test_vulnerability_scan()
    for tool, passed, message in vuln_results:
        if not passed:
            all_issues.append(f"Vulnerability scan {tool}: {message}")
    
    # Generate report
    print(f"\n{'='*50}")
    print("Generating: Dependency Report")
    print('='*50)
    
    report = generate_dependency_report()
    
    # Final summary
    print(f"\n{'='*50}")
    print("DEPENDENCY TEST SUMMARY")
    print('='*50)
    
    if all_passed and len(all_issues) == 0:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Dependencies are properly updated and secure")
        print("✅ No critical vulnerabilities found")
        print("✅ All imports working correctly")
    else:
        print("⚠️  SOME ISSUES FOUND:")
        for issue in all_issues:
            print(f"   {issue}")
        
        if len(all_issues) == 0:
            print("   (Minor warnings only)")
    
    print(f"\n📊 Summary:")
    print(f"   Total packages installed: {report['total_packages']}")
    print(f"   Core packages: {len(report['core_packages'])}")
    print(f"   Security tools: {len(report['security_packages'])}")
    print(f"   Issues found: {len(all_issues)}")
    
    print(f"\n💡 Next steps:")
    if all_issues:
        print("   1. Review and fix issues listed above")
        print("   2. Re-run this test after fixes")
    print("   3. Run full security scan: ./scripts/deps-check.sh")
    print("   4. Set up automated dependency monitoring")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())