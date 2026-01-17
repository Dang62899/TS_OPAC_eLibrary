#!/usr/bin/env python
"""
UAT Execution Tracker - Tracks and records all UAT test execution
Manages test case execution, issue logging, and status reporting
"""

import json
import os
from datetime import datetime
from pathlib import Path

class UATTracker:
    def __init__(self):
        self.data_file = "uat_execution_data.json"
        self.data = self.load_data()
    
    def load_data(self):
        """Load existing UAT data or create new"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {
            "start_date": datetime.now().isoformat(),
            "test_cases": {},
            "issues": [],
            "status": "IN_PROGRESS"
        }
    
    def save_data(self):
        """Save UAT data to file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def record_test_case(self, test_id, test_name, status, notes=""):
        """Record a test case execution"""
        self.data["test_cases"][test_id] = {
            "name": test_name,
            "status": status,  # PASSED, FAILED, BLOCKED, SKIPPED
            "timestamp": datetime.now().isoformat(),
            "notes": notes
        }
        self.save_data()
        print(f"✅ Recorded: {test_id} - {test_name} ({status})")
    
    def log_issue(self, issue_id, test_case, description, severity, assigned_to=""):
        """Log an issue found during testing"""
        issue = {
            "id": issue_id,
            "test_case": test_case,
            "description": description,
            "severity": severity,  # CRITICAL, HIGH, MEDIUM, LOW
            "assigned_to": assigned_to,
            "status": "OPEN",
            "created": datetime.now().isoformat(),
            "resolved": None
        }
        self.data["issues"].append(issue)
        self.save_data()
        print(f"⚠️  Logged issue {issue_id}: {description} ({severity})")
    
    def resolve_issue(self, issue_id, resolution):
        """Mark issue as resolved"""
        for issue in self.data["issues"]:
            if issue["id"] == issue_id:
                issue["status"] = "RESOLVED"
                issue["resolved"] = datetime.now().isoformat()
                issue["resolution"] = resolution
                self.save_data()
                print(f"✅ Resolved issue {issue_id}")
                return
        print(f"❌ Issue {issue_id} not found")
    
    def get_summary(self):
        """Get UAT execution summary"""
        total_tests = len(self.data["test_cases"])
        passed = sum(1 for t in self.data["test_cases"].values() if t["status"] == "PASSED")
        failed = sum(1 for t in self.data["test_cases"].values() if t["status"] == "FAILED")
        
        total_issues = len(self.data["issues"])
        open_issues = sum(1 for i in self.data["issues"] if i["status"] == "OPEN")
        resolved_issues = sum(1 for i in self.data["issues"] if i["status"] == "RESOLVED")
        
        critical_issues = sum(1 for i in self.data["issues"] if i["severity"] == "CRITICAL")
        
        return {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "pass_rate": (passed / total_tests * 100) if total_tests > 0 else 0,
            "total_issues": total_issues,
            "open_issues": open_issues,
            "resolved_issues": resolved_issues,
            "critical_issues": critical_issues,
            "ready_for_deployment": critical_issues == 0 and failed == 0
        }
    
    def print_status(self):
        """Print current UAT status"""
        summary = self.get_summary()
        print("\n" + "="*60)
        print("UAT EXECUTION STATUS")
        print("="*60)
        print(f"\nTest Cases: {summary['passed']}/{summary['total_tests']} PASSED ({summary['pass_rate']:.0f}%)")
        print(f"Issues: {summary['resolved_issues']} resolved, {summary['open_issues']} open")
        print(f"Critical Issues: {summary['critical_issues']}")
        print(f"\nReady for Deployment: {'✅ YES' if summary['ready_for_deployment'] else '❌ NO'}")
        print("="*60 + "\n")

def main():
    """Example usage"""
    tracker = UATTracker()
    
    # Example test case recording
    tracker.record_test_case("1.1", "Check Out Publication", "PASSED")
    tracker.record_test_case("1.2", "Return Publication", "PASSED")
    tracker.record_test_case("2.1", "Search by Title", "FAILED", "Search not returning results")
    
    # Example issue logging
    tracker.log_issue("UAT-001", "2.1", "Search endpoint returns 404", "HIGH", "Dev Team")
    
    # Print status
    tracker.print_status()

if __name__ == "__main__":
    main()
