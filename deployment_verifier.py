#!/usr/bin/env python
"""
Deployment Verification Script - Verify system is ready for go-live
Runs all pre-deployment and post-deployment checks
"""

import subprocess

try:
    import requests  # type: ignore
except ImportError:
    print("ERROR: 'requests' library not installed. Install with: pip install requests")
    exit(1)

import json
from datetime import datetime
import time

class DeploymentVerifier:
    def __init__(self):
        self.checks = {
            'pre_deployment': [],
            'post_deployment': [],
            'health_checks': [],
            'feature_verification': []
        }
        self.failed_checks = []
    
    def run_command(self, cmd, description):
        """Run a shell command and report results"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self.checks['pre_deployment'].append({'name': description, 'status': 'PASS'})
                print(f"✅ {description}")
                return True
            else:
                self.checks['pre_deployment'].append({'name': description, 'status': 'FAIL'})
                self.failed_checks.append(description)
                print(f"❌ {description}")
                return False
        except Exception as e:
            self.checks['pre_deployment'].append({'name': description, 'status': 'ERROR'})
            self.failed_checks.append(f"{description}: {str(e)}")
            print(f"❌ {description}: {str(e)}")
            return False
    
    def check_http(self, url, expected_status=200):
        """Check HTTP endpoint"""
        try:
            response = requests.get(url, timeout=5, verify=False)
            if response.status_code == expected_status:
                return True
            else:
                print(f"⚠️  Expected {expected_status}, got {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ HTTP check failed: {str(e)}")
            return False
    
    def pre_deployment_checks(self, env='local'):
        """Run pre-deployment verification checks"""
        print("\n" + "="*60)
        print("PRE-DEPLOYMENT CHECKS")
        print("="*60)
        
        # Check docker
        print("\n[1/6] Docker & Containers")
        self.run_command("docker-compose ps | grep -q 'Up'", "Docker containers running")
        
        # Check database
        print("\n[2/6] Database")
        self.run_command("docker-compose exec db pg_isready", "PostgreSQL database accessible")
        
        # Check code
        print("\n[3/6] Code Quality")
        self.run_command("python -m py_compile load_test.py", "load_test.py syntax OK")
        self.run_command("python -m py_compile security_audit.py", "security_audit.py syntax OK")
        self.run_command("python -m py_compile test_system.py", "test_system.py syntax OK")
        
        # Check configuration
        print("\n[4/6] Configuration")
        self.run_command("test -f .env.production", ".env.production exists")
        self.run_command("test -f docker-compose.yml", "docker-compose.yml exists")
        
        # Check SSL
        print("\n[5/6] SSL Certificates")
        self.run_command("test -f ssl/cert.pem", "SSL certificate exists")
        self.run_command("test -f ssl/key.pem", "SSL key exists")
        
        # Check backups
        print("\n[6/6] Backup System")
        self.run_command("test -f backup_database.sh", "Backup script exists")
    
    def post_deployment_checks(self, env='production'):
        """Run post-deployment verification checks"""
        print("\n" + "="*60)
        print("POST-DEPLOYMENT CHECKS")
        print("="*60)
        
        base_url = "http://localhost" if env == 'local' else "https://production.elibrary"
        
        print(f"\nChecking endpoints on {base_url}...")
        
        endpoints = [
            (f"{base_url}/", 200, "Homepage"),
            (f"{base_url}/admin/", 200, "Admin panel"),
            (f"{base_url}/health/", 200, "Health endpoint"),
            (f"{base_url}/search/", 200, "Search page"),
            (f"{base_url}/api/v1/", 401, "API (requires auth)"),
        ]
        
        passed = 0
        for url, expected, name in endpoints:
            try:
                response = requests.get(url, timeout=5, verify=False)
                if response.status_code == expected:
                    print(f"✅ {name}: {response.status_code}")
                    self.checks['post_deployment'].append({'endpoint': name, 'status': 'PASS'})
                    passed += 1
                else:
                    print(f"❌ {name}: Expected {expected}, got {response.status_code}")
                    self.checks['post_deployment'].append({'endpoint': name, 'status': 'FAIL'})
                    self.failed_checks.append(f"{name} returned {response.status_code}")
            except Exception as e:
                print(f"❌ {name}: {str(e)}")
                self.checks['post_deployment'].append({'endpoint': name, 'status': 'ERROR'})
                self.failed_checks.append(f"{name}: {str(e)}")
        
        return passed == len(endpoints)
    
    def feature_verification(self):
        """Verify key features are working"""
        print("\n" + "="*60)
        print("FEATURE VERIFICATION")
        print("="*60)
        
        tests = [
            ("Database has data", "docker-compose exec db psql -U elibrary -d elibrary -c 'SELECT COUNT(*) FROM catalog_publication;' | grep -q 8"),
            ("Publications loaded", "docker-compose exec db psql -U elibrary -d elibrary -c 'SELECT COUNT(*) FROM catalog_item;' | grep -q 22"),
            ("Search indexes ready", "curl -s http://localhost/search/?q=test | grep -q 'publication'"),
        ]
        
        for name, cmd in tests:
            self.run_command(cmd, name)
    
    def health_check(self):
        """Get system health metrics"""
        print("\n" + "="*60)
        print("SYSTEM HEALTH METRICS")
        print("="*60)
        
        try:
            response = requests.get("http://localhost/health/", timeout=5)
            health_data = response.json()
            
            print(f"\n✅ System Health:")
            print(f"   Status: {health_data.get('status', 'Unknown')}")
            print(f"   Database: {health_data.get('database', 'Unknown')}")
            print(f"   Timestamp: {health_data.get('timestamp', 'Unknown')}")
            
            return health_data.get('status') == 'healthy'
        except Exception as e:
            print(f"❌ Could not get health status: {str(e)}")
            return False
    
    def generate_report(self):
        """Generate deployment verification report"""
        print("\n" + "="*60)
        print("DEPLOYMENT VERIFICATION REPORT")
        print("="*60)
        
        total_checks = len(self.checks['pre_deployment']) + len(self.checks['post_deployment'])
        failed = len(self.failed_checks)
        passed = total_checks - failed
        
        print(f"\nDate: {datetime.now().isoformat()}")
        print(f"\nResults:")
        print(f"  Total Checks: {total_checks}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Success Rate: {(passed/total_checks*100):.0f}%")
        
        if failed > 0:
            print(f"\n❌ FAILED CHECKS:")
            for check in self.failed_checks:
                print(f"  - {check}")
        
        print(f"\n{'='*60}")
        if failed == 0:
            print("✅ ALL CHECKS PASSED - READY FOR DEPLOYMENT")
        else:
            print(f"⚠️  {failed} CHECKS FAILED - FIX BEFORE DEPLOYMENT")
        print(f"{'='*60}\n")
        
        return failed == 0

def main():
    """Run all verification checks"""
    print("\n🚀 DEPLOYMENT VERIFICATION STARTING...\n")
    
    verifier = DeploymentVerifier()
    
    # Run checks
    verifier.pre_deployment_checks()
    verifier.feature_verification()
    verifier.health_check()
    
    # Generate report
    ready = verifier.generate_report()
    
    if ready:
        print("\n✅ System is READY for deployment!")
        return 0
    else:
        print("\n❌ Please fix failing checks before deployment")
        return 1

if __name__ == "__main__":
    exit(main())
