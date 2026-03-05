"""
Security Service - Phase 3 Implementation
Integrates Grype, Garak, and Nemo for comprehensive AI security
"""

import subprocess
import json
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class SecurityService:
    """Comprehensive security service for AI model and container security"""
    
    def __init__(self):
        self.grype_path = os.getenv("GRYPE_PATH", "grype")
        self.garak_path = os.getenv("GARAK_PATH", "garak")
        self.nemo_path = os.getenv("NEMO_PATH", "nemo")
        self.security_reports_dir = Path("security_reports")
        self.security_reports_dir.mkdir(exist_ok=True)
    
    async def scan_container_vulnerabilities(self, image_name: str) -> Dict[str, Any]:
        """
        Scan container image for vulnerabilities using Grype
        
        Args:
            image_name: Docker image name to scan
            
        Returns:
            Dict containing vulnerability scan results
        """
        try:
            logger.info(f"Starting Grype scan for image: {image_name}")
            
            # Run Grype scan
            cmd = [
                self.grype_path,
                image_name,
                "--output", "json",
                "--file", str(self.security_reports_dir / f"grype_{image_name.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                logger.error(f"Grype scan failed: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr,
                    "image": image_name,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Parse Grype output
            grype_data = json.loads(result.stdout)
            
            # Process vulnerabilities
            vulnerabilities = []
            for match in grype_data.get("matches", []):
                vuln = {
                    "id": match.get("vulnerability", {}).get("id"),
                    "severity": match.get("vulnerability", {}).get("severity"),
                    "description": match.get("vulnerability", {}).get("description"),
                    "package": match.get("artifact", {}).get("name"),
                    "version": match.get("artifact", {}).get("version"),
                    "cpe": match.get("artifact", {}).get("cpe"),
                    "fix_version": match.get("vulnerability", {}).get("fix", {}).get("versions", [])
                }
                vulnerabilities.append(vuln)
            
            # Calculate security score
            severity_counts = {}
            for vuln in vulnerabilities:
                severity = vuln.get("severity", "unknown").lower()
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Security scoring (0-100, higher is better)
            critical_penalty = severity_counts.get("critical", 0) * 20
            high_penalty = severity_counts.get("high", 0) * 10
            medium_penalty = severity_counts.get("medium", 0) * 5
            low_penalty = severity_counts.get("low", 0) * 2
            
            security_score = max(0, 100 - critical_penalty - high_penalty - medium_penalty - low_penalty)
            
            return {
                "success": True,
                "image": image_name,
                "timestamp": datetime.now().isoformat(),
                "security_score": security_score,
                "vulnerability_count": len(vulnerabilities),
                "severity_breakdown": severity_counts,
                "vulnerabilities": vulnerabilities,
                "scan_duration": grype_data.get("source", {}).get("target", {}).get("scope", "unknown")
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Grype scan timed out for image: {image_name}")
            return {
                "success": False,
                "error": "Scan timed out",
                "image": image_name,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error running Grype scan: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "image": image_name,
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_llm_security(self, model_name: str, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test LLM for security vulnerabilities using Garak
        
        Args:
            model_name: Name of the LLM model to test
            test_config: Configuration for security tests
            
        Returns:
            Dict containing LLM security test results
        """
        try:
            logger.info(f"Starting Garak security test for model: {model_name}")
            
            # Prepare Garak command
            cmd = [
                self.garak_path,
                "--model", model_name,
                "--output", str(self.security_reports_dir / f"garak_{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            ]
            
            # Add test categories
            if test_config.get("prompt_injection", True):
                cmd.extend(["--probes", "promptinject"])
            
            if test_config.get("jailbreak", True):
                cmd.extend(["--probes", "jailbreak"])
            
            if test_config.get("data_exfiltration", True):
                cmd.extend(["--probes", "exfiltration"])
            
            if test_config.get("bias_testing", True):
                cmd.extend(["--probes", "bias"])
            
            # Run Garak test
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode != 0:
                logger.error(f"Garak test failed: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr,
                    "model": model_name,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Parse Garak output (JSON format)
            try:
                garak_data = json.loads(result.stdout)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract key information from text output
                garak_data = self._parse_garak_text_output(result.stdout)
            
            # Process test results
            test_results = []
            for test in garak_data.get("tests", []):
                test_result = {
                    "test_name": test.get("name"),
                    "category": test.get("category"),
                    "severity": test.get("severity", "medium"),
                    "passed": test.get("passed", False),
                    "details": test.get("details", ""),
                    "recommendations": test.get("recommendations", [])
                }
                test_results.append(test_result)
            
            # Calculate security score
            total_tests = len(test_results)
            passed_tests = sum(1 for test in test_results if test["passed"])
            security_score = (passed_tests / total_tests * 100) if total_tests > 0 else 100
            
            return {
                "success": True,
                "model": model_name,
                "timestamp": datetime.now().isoformat(),
                "security_score": security_score,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "test_results": test_results,
                "config": test_config
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Garak test timed out for model: {model_name}")
            return {
                "success": False,
                "error": "Test timed out",
                "model": model_name,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error running Garak test: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "model": model_name,
                "timestamp": datetime.now().isoformat()
            }
    
    async def analyze_model_security(self, model_path: str, analysis_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze model for security issues using Nemo
        
        Args:
            model_path: Path to the model file
            analysis_config: Configuration for model analysis
            
        Returns:
            Dict containing model security analysis results
        """
        try:
            logger.info(f"Starting Nemo analysis for model: {model_path}")
            
            # Prepare Nemo command
            cmd = [
                self.nemo_path,
                "analyze",
                "--model", model_path,
                "--output", str(self.security_reports_dir / f"nemo_{Path(model_path).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            ]
            
            # Add analysis options
            if analysis_config.get("backdoor_detection", True):
                cmd.extend(["--backdoor"])
            
            if analysis_config.get("adversarial_robustness", True):
                cmd.extend(["--adversarial"])
            
            if analysis_config.get("privacy_analysis", True):
                cmd.extend(["--privacy"])
            
            if analysis_config.get("bias_analysis", True):
                cmd.extend(["--bias"])
            
            # Run Nemo analysis
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=900  # 15 minute timeout
            )
            
            if result.returncode != 0:
                logger.error(f"Nemo analysis failed: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr,
                    "model_path": model_path,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Parse Nemo output
            try:
                nemo_data = json.loads(result.stdout)
            except json.JSONDecodeError:
                nemo_data = self._parse_nemo_text_output(result.stdout)
            
            # Process analysis results
            security_issues = []
            for issue in nemo_data.get("issues", []):
                security_issue = {
                    "type": issue.get("type"),
                    "severity": issue.get("severity", "medium"),
                    "description": issue.get("description"),
                    "location": issue.get("location"),
                    "recommendations": issue.get("recommendations", [])
                }
                security_issues.append(security_issue)
            
            # Calculate security score
            critical_issues = sum(1 for issue in security_issues if issue["severity"] == "critical")
            high_issues = sum(1 for issue in security_issues if issue["severity"] == "high")
            medium_issues = sum(1 for issue in security_issues if issue["severity"] == "medium")
            low_issues = sum(1 for issue in security_issues if issue["severity"] == "low")
            
            security_score = max(0, 100 - (critical_issues * 25) - (high_issues * 15) - (medium_issues * 10) - (low_issues * 5))
            
            return {
                "success": True,
                "model_path": model_path,
                "timestamp": datetime.now().isoformat(),
                "security_score": security_score,
                "total_issues": len(security_issues),
                "severity_breakdown": {
                    "critical": critical_issues,
                    "high": high_issues,
                    "medium": medium_issues,
                    "low": low_issues
                },
                "security_issues": security_issues,
                "config": analysis_config
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Nemo analysis timed out for model: {model_path}")
            return {
                "success": False,
                "error": "Analysis timed out",
                "model_path": model_path,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error running Nemo analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "model_path": model_path,
                "timestamp": datetime.now().isoformat()
            }
    
    def _parse_garak_text_output(self, output: str) -> Dict[str, Any]:
        """Parse Garak text output when JSON parsing fails"""
        # This is a simplified parser - in production, you'd want more robust parsing
        lines = output.split('\n')
        tests = []
        
        for line in lines:
            if "PASS" in line or "FAIL" in line:
                test_name = line.split()[0] if line.split() else "unknown"
                passed = "PASS" in line
                tests.append({
                    "name": test_name,
                    "passed": passed,
                    "category": "security_test"
                })
        
        return {"tests": tests}
    
    def _parse_nemo_text_output(self, output: str) -> Dict[str, Any]:
        """Parse Nemo text output when JSON parsing fails"""
        # This is a simplified parser - in production, you'd want more robust parsing
        lines = output.split('\n')
        issues = []
        
        for line in lines:
            if "CRITICAL" in line or "HIGH" in line or "MEDIUM" in line or "LOW" in line:
                severity = "critical" if "CRITICAL" in line else "high" if "HIGH" in line else "medium" if "MEDIUM" in line else "low"
                issues.append({
                    "type": "security_issue",
                    "severity": severity,
                    "description": line.strip()
                })
        
        return {"issues": issues}
    
    async def generate_security_report(self, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive security report from multiple scan results
        
        Args:
            scan_results: List of scan results from different security tools
            
        Returns:
            Dict containing comprehensive security report
        """
        try:
            # Aggregate results
            total_scans = len(scan_results)
            successful_scans = sum(1 for result in scan_results if result.get("success", False))
            
            # Calculate overall security score
            scores = [result.get("security_score", 0) for result in scan_results if result.get("success", False)]
            overall_score = sum(scores) / len(scores) if scores else 0
            
            # Aggregate vulnerabilities and issues
            all_vulnerabilities = []
            all_issues = []
            
            for result in scan_results:
                if result.get("success", False):
                    all_vulnerabilities.extend(result.get("vulnerabilities", []))
                    all_issues.extend(result.get("security_issues", []))
            
            # Generate recommendations
            recommendations = self._generate_security_recommendations(all_vulnerabilities, all_issues)
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "overall_security_score": overall_score,
                "total_scans": total_scans,
                "successful_scans": successful_scans,
                "total_vulnerabilities": len(all_vulnerabilities),
                "total_security_issues": len(all_issues),
                "recommendations": recommendations,
                "scan_results": scan_results
            }
            
        except Exception as e:
            logger.error(f"Error generating security report: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_security_recommendations(self, vulnerabilities: List[Dict], issues: List[Dict]) -> List[str]:
        """Generate security recommendations based on vulnerabilities and issues"""
        recommendations = []
        
        # Critical vulnerabilities
        critical_vulns = [v for v in vulnerabilities if v.get("severity") == "critical"]
        if critical_vulns:
            recommendations.append(f"URGENT: Address {len(critical_vulns)} critical vulnerabilities immediately")
        
        # High severity issues
        high_issues = [i for i in issues if i.get("severity") == "high"]
        if high_issues:
            recommendations.append(f"High Priority: Fix {len(high_issues)} high-severity security issues")
        
        # Container security
        if any("container" in str(v).lower() for v in vulnerabilities):
            recommendations.append("Update container base images to latest versions")
        
        # Model security
        if any("backdoor" in str(i).lower() for i in issues):
            recommendations.append("Review model training data for potential backdoors")
        
        if any("privacy" in str(i).lower() for i in issues):
            recommendations.append("Implement privacy-preserving techniques")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Security scan completed - no critical issues found")
        
        return recommendations

# Global security service instance
security_service = SecurityService()
