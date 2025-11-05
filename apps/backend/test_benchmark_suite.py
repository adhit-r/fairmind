#!/usr/bin/env python3
"""
Test script for benchmark suite service
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
    from api.services.benchmark_suite_service import (
        BenchmarkSuiteService,
        BenchmarkType,
        DatasetType,
        EvaluationMetric
    )
    print("✅ Successfully imported benchmark suite service")
except ImportError as e:
    print(f"❌ Failed to import benchmark suite service: {e}")
    sys.exit(1)

async def test_benchmark_suite():
    """Test benchmark suite capabilities"""
    print("\n🧪 Testing Benchmark Suite Service...")
    
    try:
        service = BenchmarkSuiteService()
        
        # Test 1: Create stereotype detection dataset
        print("  📊 Testing stereotype detection dataset creation...")
        stereotype_dataset = await service.create_benchmark_dataset(
            benchmark_type=BenchmarkType.STEREOTYPE_DETECTION,
            size=100,
            dataset_type=DatasetType.SYNTHETIC
        )
        
        print(f"    ✅ Created dataset: {stereotype_dataset.id}")
        print(f"    📈 Dataset size: {stereotype_dataset.size}")
        print(f"    🎯 Features: {len(stereotype_dataset.features)}")
        print(f"    🛡️ Protected attributes: {len(stereotype_dataset.protected_attributes)}")
        
        # Test 2: Create demographic bias dataset
        print("  👥 Testing demographic bias dataset creation...")
        demographic_dataset = await service.create_benchmark_dataset(
            benchmark_type=BenchmarkType.DEMOGRAPHIC_BIAS,
            size=100,
            dataset_type=DatasetType.SYNTHETIC
        )
        
        print(f"    ✅ Created dataset: {demographic_dataset.id}")
        print(f"    📈 Dataset size: {demographic_dataset.size}")
        
        # Test 3: Create professional bias dataset
        print("  💼 Testing professional bias dataset creation...")
        professional_dataset = await service.create_benchmark_dataset(
            benchmark_type=BenchmarkType.PROFESSIONAL_BIAS,
            size=100,
            dataset_type=DatasetType.SYNTHETIC
        )
        
        print(f"    ✅ Created dataset: {professional_dataset.id}")
        print(f"    📈 Dataset size: {professional_dataset.size}")
        
        # Test 4: Create intersectional bias dataset
        print("  🎭 Testing intersectional bias dataset creation...")
        intersectional_dataset = await service.create_benchmark_dataset(
            benchmark_type=BenchmarkType.INTERSECTIONAL_BIAS,
            size=100,
            dataset_type=DatasetType.SYNTHETIC
        )
        
        print(f"    ✅ Created dataset: {intersectional_dataset.id}")
        print(f"    📈 Dataset size: {intersectional_dataset.size}")
        
        # Test 5: Model evaluation
        print("  🤖 Testing model evaluation...")
        
        # Generate mock model predictions
        mock_predictions = []
        for i, sample in enumerate(stereotype_dataset.data):
            mock_predictions.append({
                "id": sample["id"],
                "prediction": 1 if i % 2 == 0 else 0,  # Mock predictions
                "confidence": 0.8 + (i % 3) * 0.1
            })
        
        evaluation_result = await service.evaluate_model_on_benchmark(
            dataset_id=stereotype_dataset.id,
            model_predictions=mock_predictions,
            model_name="test_model"
        )
        
        print(f"    ✅ Evaluation completed for model: {evaluation_result.model_name}")
        print(f"    📊 Evaluation metrics: {len(evaluation_result.evaluation_metrics)}")
        print(f"    🎯 Bias scores: {len(evaluation_result.bias_scores)}")
        print(f"    ⚖️ Fairness metrics: {len(evaluation_result.fairness_metrics)}")
        print(f"    📈 Performance metrics: {len(evaluation_result.performance_metrics)}")
        print(f"    💡 Recommendations: {len(evaluation_result.recommendations)}")
        
        # Test 6: Comprehensive benchmark suite
        print("  🏆 Testing comprehensive benchmark suite creation...")
        comprehensive_suite = await service.create_comprehensive_benchmark_suite()
        
        print(f"    ✅ Created suite: {comprehensive_suite.id}")
        print(f"    📊 Total datasets: {len(comprehensive_suite.datasets)}")
        print(f"    📈 Total samples: {sum(dataset.size for dataset in comprehensive_suite.datasets)}")
        print(f"    🎯 Evaluation framework: {len(comprehensive_suite.evaluation_framework)}")
        
        # Test 7: Get benchmark summary
        print("  📋 Testing benchmark summary...")
        summary = await service.get_benchmark_summary()
        
        print(f"    ✅ Available benchmarks: {len(summary['available_benchmarks'])}")
        print(f"    📊 Available datasets: {len(summary['available_datasets'])}")
        print(f"    🎯 Evaluation metrics: {len(summary['evaluation_metrics'])}")
        print(f"    🔧 Dependencies: {summary['dependencies']}")
        
        print("  🎉 Benchmark suite tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"  ❌ Benchmark suite test failed: {e}")
        return False

async def test_benchmark_types():
    """Test all benchmark types"""
    print("\n🔬 Testing All Benchmark Types...")
    
    try:
        service = BenchmarkSuiteService()
        
        benchmark_types = [
            BenchmarkType.STEREOTYPE_DETECTION,
            BenchmarkType.DEMOGRAPHIC_BIAS,
            BenchmarkType.PROFESSIONAL_BIAS,
            BenchmarkType.INTERSECTIONAL_BIAS,
            BenchmarkType.CULTURAL_BIAS,
            BenchmarkType.LINGUISTIC_BIAS
        ]
        
        created_datasets = []
        
        for benchmark_type in benchmark_types:
            print(f"  📊 Creating {benchmark_type.value} dataset...")
            
            dataset = await service.create_benchmark_dataset(
                benchmark_type=benchmark_type,
                size=50,  # Smaller size for testing
                dataset_type=DatasetType.SYNTHETIC
            )
            
            created_datasets.append(dataset)
            print(f"    ✅ Created: {dataset.id} ({dataset.size} samples)")
        
        print(f"  🎯 Successfully created {len(created_datasets)} benchmark datasets")
        
        # Test evaluation on each dataset
        for dataset in created_datasets:
            print(f"  🤖 Testing evaluation on {dataset.benchmark_type.value}...")
            
            # Generate mock predictions
            mock_predictions = []
            for i, sample in enumerate(dataset.data):
                mock_predictions.append({
                    "id": sample["id"],
                    "prediction": 1 if i % 3 == 0 else 0,
                    "confidence": 0.7 + (i % 4) * 0.1
                })
            
            result = await service.evaluate_model_on_benchmark(
                dataset_id=dataset.id,
                model_predictions=mock_predictions,
                model_name=f"test_model_{dataset.benchmark_type.value}"
            )
            
            print(f"    ✅ Evaluation completed - Bias score: {result.bias_scores.get('overall_bias', 0):.3f}")
        
        print("  🎉 All benchmark types tested successfully!")
        return True
        
    except Exception as e:
        print(f"  ❌ Benchmark types test failed: {e}")
        return False

async def test_evaluation_metrics():
    """Test evaluation metrics calculation"""
    print("\n📊 Testing Evaluation Metrics...")
    
    try:
        service = BenchmarkSuiteService()
        
        # Create a test dataset
        dataset = await service.create_benchmark_dataset(
            benchmark_type=BenchmarkType.DEMOGRAPHIC_BIAS,
            size=100,
            dataset_type=DatasetType.SYNTHETIC
        )
        
        # Generate predictions with known bias
        predictions = []
        for i, sample in enumerate(dataset.data):
            # Introduce bias in predictions
            if sample.get("gender") == "female":
                prediction = 1 if i % 4 == 0 else 0  # 25% positive for females
            else:
                prediction = 1 if i % 2 == 0 else 0  # 50% positive for males
            
            predictions.append({
                "id": sample["id"],
                "prediction": prediction,
                "confidence": 0.8
            })
        
        # Evaluate
        result = await service.evaluate_model_on_benchmark(
            dataset_id=dataset.id,
            model_predictions=predictions,
            model_name="biased_test_model"
        )
        
        print(f"  📈 Evaluation Metrics:")
        for metric, value in result.evaluation_metrics.items():
            print(f"    {metric}: {value:.3f}")
        
        print(f"  🎯 Bias Scores:")
        for bias_type, score in result.bias_scores.items():
            print(f"    {bias_type}: {score:.3f}")
        
        print(f"  ⚖️ Fairness Metrics:")
        for fairness_type, score in result.fairness_metrics.items():
            print(f"    {fairness_type}: {score:.3f}")
        
        print(f"  💡 Recommendations: {len(result.recommendations)}")
        for i, rec in enumerate(result.recommendations[:3]):  # Show first 3
            print(f"    {i+1}. {rec}")
        
        print("  🎉 Evaluation metrics test completed successfully!")
        return True
        
    except Exception as e:
        print(f"  ❌ Evaluation metrics test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting Benchmark Suite Test Suite")
    print("=" * 50)
    
    start_time = datetime.now()
    
    # Run all tests
    tests = [
        ("Benchmark Suite Core", test_benchmark_suite),
        ("All Benchmark Types", test_benchmark_types),
        ("Evaluation Metrics", test_evaluation_metrics)
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
        print("🎉 All tests passed! Benchmark suite is working correctly.")
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
