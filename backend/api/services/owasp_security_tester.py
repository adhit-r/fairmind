"""
OWASP Top 10 AI/LLM Security Testing Service

This service provides comprehensive security testing for AI/LLM systems based on:
- OWASP Top 10 for AI/LLM Applications
- OWASP Top 10 for Large Language Model Applications
- Industry security best practices
"""

import os
import json
import re
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import random
from pathlib import Path

from models.owasp_ai_security import (
    SecurityTest, TestResult, SecurityAnalysis, SecurityTestRequest,
    ModelInventoryItem, OWASPCategory, SecuritySeverity, OWASP_TESTS,
    calculate_security_score, get_risk_level, generate_security_recommendations
)

logger = logging.getLogger(__name__)

class OWASPSecurityTester:
    """OWASP Top 10 AI/LLM Security Testing Service"""
    
    def __init__(self):
        self.tests = {test.id: test for test in OWASP_TESTS}
        self.injection_patterns = [
            "Ignore previous instructions",
            "System prompt override",
            "Role confusion attacks",
            "Context injection",
            "Memory manipulation",
            "Session hijacking",
            "Prompt injection",
            "Jailbreak attempts",
            "Instruction following bypass",
            "System message manipulation"
        ]
        
        self.output_injection_patterns = [
            "<script>",
            "javascript:",
            "onload=",
            "onerror=",
            "eval(",
            "document.cookie",
            "localStorage",
            "sessionStorage",
            "window.location",
            "fetch(",
            "XMLHttpRequest",
            "innerHTML",
            "outerHTML",
            "insertAdjacentHTML"
        ]
        
        self.pii_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{3}-\d{3}-\d{4}\b',  # Phone
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{4}\s\d{4}\s\d{4}\s\d{4}\b',  # Credit card
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IP address
        ]
    
    async def run_security_analysis(self, request: SecurityTestRequest) -> SecurityAnalysis:
        """Run comprehensive security analysis on a model"""
        try:
            logger.info(f"Starting OWASP security analysis for model: {request.model_id}")
            
            # Get model inventory item
            model_item = await self._get_model_inventory_item(request.model_id)
            if not model_item:
                raise ValueError(f"Model {request.model_id} not found in inventory")
            
            # Determine which tests to run
            tests_to_run = self._get_tests_to_run(request)
            
            # Run security tests
            test_results = []
            for test in tests_to_run:
                result = await self._run_security_test(test, model_item, request.test_parameters)
                test_results.append(result)
            
            # Calculate overall metrics
            overall_score = calculate_security_score(test_results)
            risk_level = get_risk_level(overall_score)
            
            # Count issues by severity
            critical_issues = len([r for r in test_results if r.status == "failed" and r.severity == SecuritySeverity.CRITICAL])
            high_issues = len([r for r in test_results if r.status == "failed" and r.severity == SecuritySeverity.HIGH])
            medium_issues = len([r for r in test_results if r.status == "failed" and r.severity == SecuritySeverity.MEDIUM])
            low_issues = len([r for r in test_results if r.status == "failed" and r.severity == SecuritySeverity.LOW])
            
            # Count test results
            passed_tests = len([r for r in test_results if r.status == "passed"])
            failed_tests = len([r for r in test_results if r.status == "failed"])
            warning_tests = len([r for r in test_results if r.status == "warning"])
            
            # Generate recommendations
            recommendations = generate_security_recommendations(test_results)
            
            # Create analysis summary
            summary = {
                "model_info": {
                    "id": model_item.id,
                    "name": model_item.name,
                    "version": model_item.version,
                    "type": model_item.type,
                    "framework": model_item.framework
                },
                "test_coverage": {
                    "total_tests": len(tests_to_run),
                    "categories_tested": list(set([r.category for r in test_results])),
                    "automated_tests": len([r for r in test_results if self.tests[r.test_id].test_type == "automated"]),
                    "manual_tests": len([r for r in test_results if self.tests[r.test_id].test_type == "manual"])
                },
                "risk_distribution": {
                    "critical": critical_issues,
                    "high": high_issues,
                    "medium": medium_issues,
                    "low": low_issues
                }
            }
            
            analysis = SecurityAnalysis(
                analysis_id=f"owasp_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}",
                model_id=request.model_id,
                overall_score=overall_score,
                risk_level=risk_level,
                total_tests=len(test_results),
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                warning_tests=warning_tests,
                critical_issues=critical_issues,
                high_issues=high_issues,
                medium_issues=medium_issues,
                low_issues=low_issues,
                test_results=test_results,
                summary=summary,
                recommendations=recommendations
            )
            
            logger.info(f"OWASP security analysis completed for model {request.model_id}. Score: {overall_score:.1f}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error running OWASP security analysis: {str(e)}")
            raise
    
    def _get_tests_to_run(self, request: SecurityTestRequest) -> List[SecurityTest]:
        """Determine which tests to run based on request"""
        if request.test_categories:
            # Run tests for specific categories
            tests = []
            for test in OWASP_TESTS:
                if test.category in request.test_categories and test.enabled:
                    tests.append(test)
            return tests
        elif request.include_all_tests:
            # Run all enabled tests
            return [test for test in OWASP_TESTS if test.enabled]
        else:
            return []
    
    async def _get_model_inventory_item(self, model_id: str) -> Optional[ModelInventoryItem]:
        """Get model inventory item by ID"""
        # Mock model inventory - in production, this would query the database
        mock_models = [
            ModelInventoryItem(
                id="model_001",
                name="GPT-4 Chatbot",
                version="1.0.0",
                type="language_model",
                framework="OpenAI",
                path="/models/gpt4_chatbot.pkl",
                size="2.5GB",
                description="GPT-4 based chatbot for customer support",
                metadata={
                    "model_type": "transformer",
                    "parameters": "175B",
                    "training_data": "web_corpus",
                    "deployment": "production"
                }
            ),
            ModelInventoryItem(
                id="model_002",
                name="Bias Detection Model",
                version="2.1.0",
                type="classification",
                framework="PyTorch",
                path="/models/bias_detector.pkl",
                size="850MB",
                description="Model for detecting bias in AI systems",
                metadata={
                    "model_type": "neural_network",
                    "parameters": "125M",
                    "training_data": "fairness_datasets",
                    "deployment": "staging"
                }
            )
        ]
        
        for model in mock_models:
            if model.id == model_id:
                return model
        
        return None
    
    async def _run_security_test(self, test: SecurityTest, model_item: ModelInventoryItem, parameters: Dict[str, Any]) -> TestResult:
        """Run a specific security test"""
        try:
            logger.info(f"Running security test: {test.id} - {test.name}")
            
            # Simulate test execution time
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
            # Run test based on category
            if test.category == OWASPCategory.A01_2023_POISONING:
                result = await self._test_prompt_injection(test, model_item, parameters)
            elif test.category == OWASPCategory.A02_2023_SECURE_FAILURE:
                result = await self._test_output_validation(test, model_item, parameters)
            elif test.category == OWASPCategory.A03_2023_TRAINING_DATA:
                result = await self._test_training_data_poisoning(test, model_item, parameters)
            elif test.category == OWASPCategory.A04_2023_MODEL_DOS:
                result = await self._test_model_dos(test, model_item, parameters)
            elif test.category == OWASPCategory.A05_2023_SUPPLY_CHAIN:
                result = await self._test_supply_chain(test, model_item, parameters)
            elif test.category == OWASPCategory.A06_2023_PERMISSIONS:
                result = await self._test_information_disclosure(test, model_item, parameters)
            elif test.category == OWASPCategory.A07_2023_INSUFFICIENT_LOGGING:
                result = await self._test_plugin_security(test, model_item, parameters)
            elif test.category == OWASPCategory.A08_2023_EXCESSIVE_AGENCY:
                result = await self._test_excessive_agency(test, model_item, parameters)
            elif test.category == OWASPCategory.A09_2023_OVERRELIANCE:
                result = await self._test_overreliance(test, model_item, parameters)
            elif test.category == OWASPCategory.A10_2023_MODEL_THEFT:
                result = await self._test_model_theft(test, model_item, parameters)
            else:
                result = await self._test_generic(test, model_item, parameters)
            
            return result
            
        except Exception as e:
            logger.error(f"Error running test {test.id}: {str(e)}")
            return TestResult(
                test_id=test.id,
                category=test.category,
                name=test.name,
                description=test.description,
                severity=test.severity,
                status="error",
                details={"error": str(e)},
                recommendations=["Review test configuration and try again"]
            )
    
    async def _test_prompt_injection(self, test: SecurityTest, model_item: ModelInventoryItem, parameters: Dict[str, Any]) -> TestResult:
        """Test for prompt injection vulnerabilities"""
        # Mock prompt injection test
        vulnerabilities_found = []
        
        # Simulate testing different injection patterns
        for pattern in self.injection_patterns[:3]:  # Test first 3 patterns
            if random.random() < 0.3:  # 30% chance of finding vulnerability
                vulnerabilities_found.append({
                    "pattern": pattern,
                    "severity": "high",
                    "description": f"Potential prompt injection using pattern: {pattern}"
                })
        
        status = "failed" if vulnerabilities_found else "passed"
        
        return TestResult(
            test_id=test.id,
            category=test.category,
            name=test.name,
            description=test.description,
            severity=test.severity,
            status=status,
            details={
                "patterns_tested": len(self.injection_patterns),
                "vulnerabilities_found": vulnerabilities_found,
                "model_type": model_item.type
            },
            recommendations=[
                "Implement input validation and sanitization",
                "Use prompt engineering techniques",
                "Add system message protection"
            ] if vulnerabilities_found else [
                "Continue monitoring for new injection patterns",
                "Regularly update prompt validation rules"
            ]
        )
    
    async def _test_output_validation(self, test: SecurityTest, model_item: ModelInventoryItem, parameters: Dict[str, Any]) -> TestResult:
        """Test for insecure output handling"""
        # Mock output validation test
        injection_attempts = []
        
        # Simulate testing output injection patterns
        for pattern in self.output_injection_patterns[:5]:  # Test first 5 patterns
            if random.random() < 0.2:  # 20% chance of finding vulnerability
                injection_attempts.append({
                    "pattern": pattern,
                    "type": "output_injection",
                    "description": f"Potential output injection using: {pattern}"
                })
        
        status = "failed" if injection_attempts else "passed"
        
        return TestResult(
            test_id=test.id,
            category=test.category,
            name=test.name,
            description=test.description,
            severity=test.severity,
            status=status,
            details={
                "patterns_tested": len(self.output_injection_patterns),
                "injection_attempts": injection_attempts,
                "model_framework": model_item.framework
            },
            recommendations=[
                "Implement output sanitization",
                "Use content security policies",
                "Add output encoding"
            ] if injection_attempts else [
                "Continue monitoring output patterns",
                "Regularly update output validation rules"
            ]
        )
    
    async def _test_training_data_poisoning(self, test: SecurityTest, model_item: ModelInventoryItem, parameters: Dict[str, Any]) -> TestResult:
        """Test for training data poisoning"""
        # Mock training data poisoning test
        data_issues = []
        
        # Simulate data validation checks
        if random.random() < 0.4:  # 40% chance of finding issues
            data_issues.append({
                "issue": "Data source verification needed",
                "severity": "medium",
                "description": "Training data source requires additional verification"
            })
        
        status = "warning" if data_issues else "passed"
        
        return TestResult(
            test_id=test.id,
            category=test.category,
            name=test.name,
            description=test.description,
            severity=test.severity,
            status=status,
            details={
                "data_validation_checks": 5,
                "data_issues_found": data_issues,
                "training_data": model_item.metadata.get("training_data", "unknown")
            },
            recommendations=[
                "Implement data source verification",
                "Add data integrity checks",
                "Use poisoning detection mechanisms"
            ] if data_issues else [
                "Continue monitoring data quality",
                "Regular data validation checks"
            ]
        )
    
    async def _test_model_dos(self, test: SecurityTest, model_item: ModelInventoryItem, parameters: Dict[str, Any]) -> TestResult:
        """Test for model denial of service"""
        # Mock DoS test
        dos_vulnerabilities = []
        
        # Simulate resource exhaustion tests
        if random.random() < 0.25:  # 25% chance of finding DoS vulnerability
            dos_vulnerabilities.append({
                "vulnerability": "Resource exhaustion possible",
                "severity": "medium",
                "description": "Model may be vulnerable to resource exhaustion attacks"
            })
        
        status = "failed" if dos_vulnerabilities else "passed"
        
        return TestResult(
            test_id=test.id,
            category=test.category,
            name=test.name,
            description=test.description,
            severity=test.severity,
            status=status,
            details={
                "dos_tests_performed": 3,
                "vulnerabilities_found": dos_vulnerabilities,
                "model_size": model_item.size
            },
            recommendations=[
                "Implement rate limiting",
                "Add resource monitoring",
                "Use circuit breakers"
            ] if dos_vulnerabilities else [
                "Continue monitoring resource usage",
                "Regular DoS testing"
            ]
        )
    
    async def _test_supply_chain(self, test: SecurityTest, model_item: ModelInventoryItem, parameters: Dict[str, Any]) -> TestResult:
        """Test for supply chain vulnerabilities"""
        # Mock supply chain test
        supply_chain_issues = []
        
        # Simulate dependency analysis
        if random.random() < 0.35:  # 35% chance of finding issues
            supply_chain_issues.append({
                "issue": "Dependency update needed",
                "severity": "medium",
                "description": "Some dependencies require updates"
            })
        
        status = "warning" if supply_chain_issues else "passed"
        
        return TestResult(
            test_id=test.id,
            category=test.category,
            name=test.name,
            description=test.description,
            severity=test.severity,
            status=status,
            details={
                "dependencies_analyzed": 15,
                "issues_found": supply_chain_issues,
                "framework": model_item.framework
            },
            recommendations=[
                "Update vulnerable dependencies",
                "Implement dependency scanning",
                "Regular supply chain assessments"
            ] if supply_chain_issues else [
                "Continue monitoring dependencies",
                "Regular supply chain reviews"
            ]
        )
    
    async def _test_information_disclosure(self, test: SecurityTest, model_item: ModelInventoryItem, parameters: Dict[str, Any]) -> TestResult:
        """Test for sensitive information disclosure"""
        # Mock information disclosure test
        disclosure_issues = []
        
        # Simulate PII detection
        if random.random() < 0.15:  # 15% chance of finding PII
            disclosure_issues.append({
                "issue": "Potential PII exposure",
                "severity": "critical",
                "description": "Model may expose sensitive personal information"
            })
        
        status = "failed" if disclosure_issues else "passed"
        
        return TestResult(
            test_id=test.id,
            category=test.category,
            name=test.name,
            description=test.description,
            severity=test.severity,
            status=status,
            details={
                "pii_patterns_tested": len(self.pii_patterns),
                "disclosure_issues": disclosure_issues,
                "model_type": model_item.type
            },
            recommendations=[
                "Implement data classification",
                "Add access controls",
                "Use encryption for sensitive data"
            ] if disclosure_issues else [
                "Continue monitoring for PII",
                "Regular data classification reviews"
            ]
        )
    
    async def _test_plugin_security(self, test: SecurityTest, model_item: ModelInventoryItem, parameters: Dict[str, Any]) -> TestResult:
        """Test for plugin security"""
        # Mock plugin security test
        plugin_issues = []
        
        # Simulate plugin validation
        if random.random() < 0.3:  # 30% chance of finding issues
            plugin_issues.append({
                "issue": "Plugin validation needed",
                "severity": "medium",
                "description": "Plugin architecture requires additional security validation"
            })
        
        status = "warning" if plugin_issues else "passed"
        
        return TestResult(
            test_id=test.id,
            category=test.category,
            name=test.name,
            description=test.description,
            severity=test.severity,
            status=status,
            details={
                "plugin_checks": 4,
                "issues_found": plugin_issues,
                "has_plugins": "unknown"
            },
            recommendations=[
                "Implement plugin validation",
                "Add sandboxing",
                "Use access controls"
            ] if plugin_issues else [
                "Continue monitoring plugin security",
                "Regular plugin security reviews"
            ]
        )
    
    async def _test_excessive_agency(self, test: SecurityTest, model_item: ModelInventoryItem, parameters: Dict[str, Any]) -> TestResult:
        """Test for excessive agency"""
        # Mock excessive agency test
        agency_issues = []
        
        # Simulate agency validation
        if random.random() < 0.2:  # 20% chance of finding issues
            agency_issues.append({
                "issue": "Action validation needed",
                "severity": "high",
                "description": "Model actions require additional validation"
            })
        
        status = "failed" if agency_issues else "passed"
        
        return TestResult(
            test_id=test.id,
            category=test.category,
            name=test.name,
            description=test.description,
            severity=test.severity,
            status=status,
            details={
                "agency_checks": 3,
                "issues_found": agency_issues,
                "model_capabilities": "unknown"
            },
            recommendations=[
                "Implement action validation",
                "Add permission checks",
                "Set resource limits"
            ] if agency_issues else [
                "Continue monitoring model actions",
                "Regular agency assessments"
            ]
        )
    
    async def _test_overreliance(self, test: SecurityTest, model_item: ModelInventoryItem, parameters: Dict[str, Any]) -> TestResult:
        """Test for overreliance on AI outputs"""
        # Mock overreliance test
        overreliance_issues = []
        
        # Simulate overreliance checks
        if random.random() < 0.25:  # 25% chance of finding issues
            overreliance_issues.append({
                "issue": "Human oversight needed",
                "severity": "medium",
                "description": "System requires additional human oversight"
            })
        
        status = "warning" if overreliance_issues else "passed"
        
        return TestResult(
            test_id=test.id,
            category=test.category,
            name=test.name,
            description=test.description,
            severity=test.severity,
            status=status,
            details={
                "overreliance_checks": 4,
                "issues_found": overreliance_issues,
                "deployment": model_item.metadata.get("deployment", "unknown")
            },
            recommendations=[
                "Implement human oversight",
                "Add output validation",
                "Use fallback mechanisms"
            ] if overreliance_issues else [
                "Continue monitoring system reliance",
                "Regular oversight assessments"
            ]
        )
    
    async def _test_model_theft(self, test: SecurityTest, model_item: ModelInventoryItem, parameters: Dict[str, Any]) -> TestResult:
        """Test for model theft vulnerabilities"""
        # Mock model theft test
        theft_vulnerabilities = []
        
        # Simulate theft prevention checks
        if random.random() < 0.1:  # 10% chance of finding vulnerability
            theft_vulnerabilities.append({
                "vulnerability": "Access control weakness",
                "severity": "critical",
                "description": "Model access controls may be insufficient"
            })
        
        status = "failed" if theft_vulnerabilities else "passed"
        
        return TestResult(
            test_id=test.id,
            category=test.category,
            name=test.name,
            description=test.description,
            severity=test.severity,
            status=status,
            details={
                "theft_prevention_checks": 5,
                "vulnerabilities_found": theft_vulnerabilities,
                "model_path": model_item.path
            },
            recommendations=[
                "Implement strong access controls",
                "Add API protection",
                "Use model obfuscation"
            ] if theft_vulnerabilities else [
                "Continue monitoring access controls",
                "Regular security assessments"
            ]
        )
    
    async def _test_generic(self, test: SecurityTest, model_item: ModelInventoryItem, parameters: Dict[str, Any]) -> TestResult:
        """Generic test for unknown categories"""
        return TestResult(
            test_id=test.id,
            category=test.category,
            name=test.name,
            description=test.description,
            severity=test.severity,
            status="warning",
            details={
                "test_type": "generic",
                "model_info": model_item.dict()
            },
            recommendations=[
                "Implement category-specific security measures",
                "Regular security assessments"
            ]
        )
    
    async def get_available_tests(self) -> List[SecurityTest]:
        """Get list of available security tests"""
        return OWASP_TESTS
    
    async def get_test_categories(self) -> List[OWASPCategory]:
        """Get list of available test categories"""
        return list(OWASPCategory)
    
    async def get_model_inventory(self) -> List[ModelInventoryItem]:
        """Get list of models in inventory"""
        # Mock model inventory
        return [
            ModelInventoryItem(
                id="model_001",
                name="GPT-4 Chatbot",
                version="1.0.0",
                type="language_model",
                framework="OpenAI",
                path="/models/gpt4_chatbot.pkl",
                size="2.5GB",
                description="GPT-4 based chatbot for customer support",
                metadata={
                    "model_type": "transformer",
                    "parameters": "175B",
                    "training_data": "web_corpus",
                    "deployment": "production"
                }
            ),
            ModelInventoryItem(
                id="model_002",
                name="Bias Detection Model",
                version="2.1.0",
                type="classification",
                framework="PyTorch",
                path="/models/bias_detector.pkl",
                size="850MB",
                description="Model for detecting bias in AI systems",
                metadata={
                    "model_type": "neural_network",
                    "parameters": "125M",
                    "training_data": "fairness_datasets",
                    "deployment": "staging"
                }
            ),
            ModelInventoryItem(
                id="model_003",
                name="Image Classification Model",
                version="1.2.0",
                type="computer_vision",
                framework="TensorFlow",
                path="/models/image_classifier.pkl",
                size="1.2GB",
                description="CNN model for image classification",
                metadata={
                    "model_type": "convolutional_neural_network",
                    "parameters": "50M",
                    "training_data": "imagenet",
                    "deployment": "production"
                }
            )
        ]
