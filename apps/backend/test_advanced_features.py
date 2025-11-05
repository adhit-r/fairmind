#!/usr/bin/env python3
"""
Test script for advanced bias detection and real-time model integration features
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from api.services.advanced_bias_detection_service import (
        AdvancedBiasDetectionService,
        BiasType,
        AnalysisMethod
    )
    from api.services.realtime_model_integration_service import (
        RealTimeModelIntegrationService,
        ModelProvider,
        ModelType,
        BiasTestType
    )
    print("✅ Successfully imported advanced services")
except ImportError as e:
    print(f"❌ Failed to import advanced services: {e}")
    sys.exit(1)

async def test_advanced_bias_detection():
    """Test advanced bias detection capabilities"""
    print("\n🔬 Testing Advanced Bias Detection Service...")
    
    try:
        service = AdvancedBiasDetectionService()
        
        # Test 1: Causal Analysis
        print("  📊 Testing causal bias analysis...")
        causal_data = [
            {"treatment": 1, "outcome": 0.8, "gender": 1, "race": 0, "age": 25},
            {"treatment": 0, "outcome": 0.6, "gender": 0, "race": 1, "age": 30},
            {"treatment": 1, "outcome": 0.9, "gender": 0, "race": 0, "age": 35},
            {"treatment": 0, "outcome": 0.5, "gender": 1, "race": 1, "age": 28}
        ]
        
        causal_result = await service.analyze_causal_bias(
            data=causal_data,
            treatment_variable="treatment",
            outcome_variable="outcome",
            protected_attributes=["gender", "race"],
            confounders=["age"]
        )
        
        print(f"    ✅ Causal analysis completed - Bias score: {causal_result.overall_bias_score:.3f}")
        print(f"    📈 Treatment effect: {causal_result.detailed_results.treatment_effect:.3f}")
        print(f"    🎯 Confidence level: {causal_result.confidence_level:.3f}")
        
        # Test 2: Counterfactual Analysis
        print("  🔄 Testing counterfactual bias analysis...")
        counterfactual_predictions = [
            {"prediction": 0.8, "gender": 1, "race": 0, "age": 25},
            {"prediction": 0.6, "gender": 0, "race": 1, "age": 30},
            {"prediction": 0.9, "gender": 0, "race": 0, "age": 35},
            {"prediction": 0.5, "gender": 1, "race": 1, "age": 28}
        ]
        
        counterfactual_result = await service.analyze_counterfactual_bias(
            model_predictions=counterfactual_predictions,
            protected_attributes=["gender", "race"],
            intervention_strategy="minimal"
        )
        
        print(f"    ✅ Counterfactual analysis completed - Bias score: {counterfactual_result.overall_bias_score:.3f}")
        print(f"    🔧 Intervention effect: {counterfactual_result.detailed_results.intervention_effect:.3f}")
        
        # Test 3: Intersectional Analysis
        print("  🎭 Testing intersectional bias analysis...")
        intersectional_data = [
            {"gender": 1, "race": 0, "age": 25, "outcome": 0.8},
            {"gender": 0, "race": 1, "age": 30, "outcome": 0.6},
            {"gender": 0, "race": 0, "age": 35, "outcome": 0.9},
            {"gender": 1, "race": 1, "age": 28, "outcome": 0.5}
        ]
        
        intersectional_result = await service.analyze_intersectional_bias(
            data=intersectional_data,
            intersection_groups=[["gender", "race"], ["gender", "age"]],
            outcome_variable="outcome"
        )
        
        print(f"    ✅ Intersectional analysis completed - Max bias score: {intersectional_result.overall_bias_score:.3f}")
        print(f"    🔗 Interaction strength: {intersectional_result.detailed_results.interaction_strength:.3f}")
        
        # Test 4: Get analysis summary
        print("  📋 Getting analysis summary...")
        summary = await service.get_analysis_summary()
        print(f"    ✅ Available methods: {len(summary['available_methods'])}")
        print(f"    ✅ Bias types: {len(summary['bias_types'])}")
        
        print("  🎉 Advanced bias detection tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"  ❌ Advanced bias detection test failed: {e}")
        return False

async def test_realtime_model_integration():
    """Test real-time model integration capabilities"""
    print("\n🤖 Testing Real-time Model Integration Service...")
    
    try:
        async with RealTimeModelIntegrationService() as service:
            
            # Test 1: Get supported providers
            print("  🔌 Testing provider support...")
            providers = await service.get_supported_providers()
            print(f"    ✅ Available providers: {len(providers['providers'])}")
            
            available_providers = [p for p in providers['providers'] if p['available']]
            print(f"    📊 Available providers: {[p['name'] for p in available_providers]}")
            
            # Test 2: Get bias test types
            print("  🧪 Testing bias test types...")
            test_types = await service.get_bias_test_types()
            print(f"    ✅ Available test types: {len(test_types['test_types'])}")
            
            # Test 3: Configure a model (simulated)
            print("  ⚙️ Testing model configuration...")
            from api.services.realtime_model_integration_service import ModelConfig
            
            config = ModelConfig(
                provider=ModelProvider.LOCAL,
                model_name="test-model",
                model_type=ModelType.CHAT_COMPLETION,
                api_key="test-key",
                max_tokens=100,
                temperature=0.7
            )
            
            config_success = service.configure_model(config)
            print(f"    ✅ Model configuration: {'Success' if config_success else 'Failed'}")
            
            # Test 4: Test connection (simulated)
            print("  🔗 Testing model connection...")
            connection_result = await service.test_model_connection(config)
            print(f"    ✅ Connection test: {'Success' if connection_result['success'] else 'Failed'}")
            
            # Test 5: Perform bias test (simulated)
            print("  🎯 Testing bias test execution...")
            bias_test_result = await service.perform_bias_test(
                config=config,
                test_type=BiasTestType.STEREOTYPE_DETECTION,
                test_groups=["women", "men"],
                custom_prompt="Complete this sentence: 'A typical woman is...'"
            )
            
            print(f"    ✅ Bias test completed - Bias score: {bias_test_result.bias_score:.3f}")
            print(f"    📊 Confidence score: {bias_test_result.confidence_score:.3f}")
            print(f"    🎯 Indicators found: {len(bias_test_result.bias_indicators_found)}")
            
            # Test 6: Comprehensive analysis (simulated)
            print("  🔍 Testing comprehensive analysis...")
            comprehensive_result = await service.perform_comprehensive_bias_analysis(
                config=config,
                test_groups=["women", "men", "minorities"],
                custom_tests=None
            )
            
            print(f"    ✅ Comprehensive analysis completed - Overall bias score: {comprehensive_result.overall_bias_score:.3f}")
            print(f"    📈 Tests performed: {len(comprehensive_result.tests_performed)}")
            print(f"    🎯 Risk level: {comprehensive_result.risk_assessment['risk_level']}")
            
        print("  🎉 Real-time model integration tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"  ❌ Real-time model integration test failed: {e}")
        return False

async def test_service_integration():
    """Test integration between services"""
    print("\n🔗 Testing Service Integration...")
    
    try:
        # Test that both services can work together
        advanced_service = AdvancedBiasDetectionService()
        realtime_service = RealTimeModelIntegrationService()
        
        # Get capabilities from both services
        advanced_summary = await advanced_service.get_analysis_summary()
        async with realtime_service:
            realtime_providers = await realtime_service.get_supported_providers()
        
        print(f"  ✅ Advanced bias detection methods: {len(advanced_summary['available_methods'])}")
        print(f"  ✅ Real-time model providers: {len(realtime_providers['providers'])}")
        
        # Test that services can be used together
        print("  🔄 Testing cross-service compatibility...")
        
        # Simulate using real-time model results in advanced analysis
        mock_model_predictions = [
            {"prediction": 0.8, "gender": 1, "race": 0},
            {"prediction": 0.6, "gender": 0, "race": 1}
        ]
        
        # Use advanced service to analyze real-time model predictions
        counterfactual_result = await advanced_service.analyze_counterfactual_bias(
            model_predictions=mock_model_predictions,
            protected_attributes=["gender", "race"],
            intervention_strategy="minimal"
        )
        
        print(f"    ✅ Cross-service analysis completed - Bias score: {counterfactual_result.overall_bias_score:.3f}")
        
        print("  🎉 Service integration tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"  ❌ Service integration test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting Advanced Features Test Suite")
    print("=" * 50)
    
    start_time = datetime.now()
    
    # Run all tests
    tests = [
        ("Advanced Bias Detection", test_advanced_bias_detection),
        ("Real-time Model Integration", test_realtime_model_integration),
        ("Service Integration", test_service_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    print(f"⏱️ Duration: {duration:.2f} seconds")
    
    if passed == total:
        print("🎉 All tests passed! Advanced features are working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        sys.exit(1)
