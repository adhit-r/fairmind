#!/usr/bin/env python3
"""
Simple test script for modern bias detection capabilities
Tests core functionality without external dependencies
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_bias_categories():
    """Test bias category definitions"""
    print("Testing bias categories...")
    
    # Import the bias categories
    try:
        from api.services.modern_llm_bias_service import BiasCategory, ExplainabilityMethod
        
        print(f"Available bias categories: {[cat.value for cat in BiasCategory]}")
        print(f"Available explainability methods: {[method.value for method in ExplainabilityMethod]}")
        
        return True
    except Exception as e:
        print(f"Error testing bias categories: {e}")
        return False

def test_evaluation_phases():
    """Test evaluation phase definitions"""
    print("\nTesting evaluation phases...")
    
    try:
        from api.services.comprehensive_bias_evaluation_pipeline import EvaluationPhase, BiasRiskLevel
        
        print(f"Available evaluation phases: {[phase.value for phase in EvaluationPhase]}")
        print(f"Available risk levels: {[level.value for level in BiasRiskLevel]}")
        
        return True
    except Exception as e:
        print(f"Error testing evaluation phases: {e}")
        return False

def test_tool_configurations():
    """Test tool configuration structures"""
    print("\nTesting tool configurations...")
    
    try:
        # Test that we can import the service classes
        from api.services.modern_llm_bias_service import ModernLLMBiasService
        from api.services.modern_tools_integration import ModernToolsIntegrationService
        from api.services.comprehensive_bias_evaluation_pipeline import ComprehensiveBiasEvaluationPipeline
        
        # Test initialization
        bias_service = ModernLLMBiasService()
        print(f"Bias tests configured: {len(bias_service.bias_tests)}")
        print(f"Explainability methods configured: {len(bias_service.explainability_methods)}")
        print(f"Evaluation datasets configured: {len(bias_service.evaluation_datasets)}")
        
        # Test tool integration service
        tools_service = ModernToolsIntegrationService()
        print(f"Tools configured: {len(tools_service.tool_configs)}")
        
        # Test evaluation pipeline
        pipeline = ComprehensiveBiasEvaluationPipeline()
        print(f"Evaluation configs: {len(pipeline.evaluation_configs)}")
        print(f"Monitoring thresholds: {len(pipeline.monitoring_thresholds)}")
        print(f"Compliance frameworks: {len(pipeline.compliance_frameworks)}")
        
        return True
    except Exception as e:
        print(f"Error testing tool configurations: {e}")
        return False

def test_api_routes():
    """Test API route imports"""
    print("\nTesting API route imports...")
    
    try:
        from api.routes.modern_bias_detection import router as bias_router
        from api.routes.modern_tools_integration import router as tools_router
        from api.routes.comprehensive_bias_evaluation import router as evaluation_router
        
        print(f"Modern bias detection routes: {len(bias_router.routes)}")
        print(f"Modern tools integration routes: {len(tools_router.routes)}")
        print(f"Comprehensive evaluation routes: {len(evaluation_router.routes)}")
        
        return True
    except Exception as e:
        print(f"Error testing API routes: {e}")
        return False

def test_bias_test_configurations():
    """Test bias test configurations"""
    print("\nTesting bias test configurations...")
    
    try:
        from api.services.modern_llm_bias_service import ModernLLMBiasService
        
        bias_service = ModernLLMBiasService()
        
        # Test bias tests
        print("Bias Tests:")
        for test_id, config in bias_service.bias_tests.items():
            print(f"  - {test_id}: {config['name']} ({config['category'].value})")
        
        # Test explainability methods
        print("\nExplainability Methods:")
        for method_id, config in bias_service.explainability_methods.items():
            print(f"  - {method_id}: {config['name']}")
        
        # Test evaluation datasets
        print("\nEvaluation Datasets:")
        for dataset_id, config in bias_service.evaluation_datasets.items():
            print(f"  - {dataset_id}: {config['name']}")
        
        return True
    except Exception as e:
        print(f"Error testing bias test configurations: {e}")
        return False

def test_tool_integration_configurations():
    """Test tool integration configurations"""
    print("\nTesting tool integration configurations...")
    
    try:
        from api.services.modern_tools_integration import ModernToolsIntegrationService
        
        tools_service = ModernToolsIntegrationService()
        
        print("Available Tools:")
        for tool_id, config in tools_service.tool_configs.items():
            print(f"  - {tool_id}: {config['name']}")
            print(f"    Description: {config['description']}")
            print(f"    Enabled: {config['enabled']}")
            print(f"    Features: {config['features']}")
            print()
        
        return True
    except Exception as e:
        print(f"Error testing tool integration configurations: {e}")
        return False

def test_evaluation_pipeline_configurations():
    """Test evaluation pipeline configurations"""
    print("\nTesting evaluation pipeline configurations...")
    
    try:
        from api.services.comprehensive_bias_evaluation_pipeline import ComprehensiveBiasEvaluationPipeline
        
        pipeline = ComprehensiveBiasEvaluationPipeline()
        
        print("Evaluation Phases:")
        for phase, config in pipeline.evaluation_configs.items():
            print(f"  - {phase}:")
            print(f"    Enabled: {config.get('enabled', False)}")
            if 'required_tests' in config:
                print(f"    Required Tests: {config['required_tests']}")
            if 'monitoring_interval_minutes' in config:
                print(f"    Monitoring Interval: {config['monitoring_interval_minutes']} minutes")
            if 'audit_frequency_days' in config:
                print(f"    Audit Frequency: {config['audit_frequency_days']} days")
            print()
        
        print("Monitoring Thresholds:")
        for bias_type, thresholds in pipeline.monitoring_thresholds.items():
            print(f"  - {bias_type}: {thresholds}")
        
        print("\nCompliance Frameworks:")
        for framework, config in pipeline.compliance_frameworks.items():
            print(f"  - {framework}:")
            print(f"    Enabled: {config['enabled']}")
            print(f"    Requirements: {config['requirements']}")
            print()
        
        return True
    except Exception as e:
        print(f"Error testing evaluation pipeline configurations: {e}")
        return False

def main():
    """Main test function"""
    print("Modern Bias Detection and Explainability - Simple Test Suite")
    print("Testing core functionality without external dependencies")
    print("=" * 80)
    
    tests = [
        ("Bias Categories", test_bias_categories),
        ("Evaluation Phases", test_evaluation_phases),
        ("Tool Configurations", test_tool_configurations),
        ("API Routes", test_api_routes),
        ("Bias Test Configurations", test_bias_test_configurations),
        ("Tool Integration Configurations", test_tool_integration_configurations),
        ("Evaluation Pipeline Configurations", test_evaluation_pipeline_configurations)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results[test_name] = "PASS" if success else "FAIL"
            print(f"✅ {test_name}: {'PASS' if success else 'FAIL'}")
        except Exception as e:
            results[test_name] = f"ERROR: {e}"
            print(f"❌ {test_name}: ERROR - {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for result in results.values() if result == "PASS")
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result == "PASS" else "❌"
        print(f"{status} {test_name}: {result}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The modern bias detection system is properly configured.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    # Save results
    results_summary = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": total,
        "passed_tests": passed,
        "test_results": results
    }
    
    with open("simple_test_results.json", "w") as f:
        json.dump(results_summary, f, indent=2)
    
    print(f"\nResults saved to: simple_test_results.json")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

