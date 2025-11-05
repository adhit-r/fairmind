"""
Test Script for Phase 2 - ML Simulation Engine
Verifies that all components are working correctly
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_phase2_components():
    """Test all Phase 2 components"""
    print("🧪 Testing FairMind Phase 2 Components...")
    print("=" * 50)
    
    try:
        # Test 1: Import simulation service
        print("1. Testing Simulation Service Import...")
        from api.services.simulation_service import simulation_service, SimulationConfig
        print("   ✅ Simulation service imported successfully")
        
        # Test 2: Check available algorithms
        print("\n2. Testing Available Algorithms...")
        classification_algs = list(simulation_service.classification_algorithms.keys())
        regression_algs = list(simulation_service.regression_algorithms.keys())
        print(f"   ✅ Classification algorithms: {classification_algs}")
        print(f"   ✅ Regression algorithms: {regression_algs}")
        
        # Test 3: Test dataset service
        print("\n3. Testing Dataset Service...")
        from api.services.dataset_service import dataset_service
        print(f"   ✅ Dataset service initialized")
        print(f"   ✅ Upload directory: {dataset_service.upload_dir}")
        print(f"   ✅ Max file size: {dataset_service.max_file_size // (1024*1024)}MB")
        
        # Test 4: Check directories
        print("\n4. Testing Directory Structure...")
        models_dir = simulation_service.models_dir
        results_dir = simulation_service.results_dir
        
        models_dir.mkdir(exist_ok=True)
        results_dir.mkdir(exist_ok=True)
        
        print(f"   ✅ Models directory: {models_dir}")
        print(f"   ✅ Results directory: {results_dir}")
        
        # Test 5: Test configuration validation
        print("\n5. Testing Configuration Validation...")
        config = SimulationConfig(
            model_type="regression",
            algorithm="random_forest",
            target_column="income",
            feature_columns=["age", "education"],
            protected_attributes=["gender"]
        )
        print(f"   ✅ Configuration created: {config.model_type} - {config.algorithm}")
        
        # Test 6: Check sample dataset
        print("\n6. Testing Sample Dataset...")
        sample_path = Path("sample_datasets/sample_income_data.csv")
        if sample_path.exists():
            print(f"   ✅ Sample dataset found: {sample_path}")
            print(f"   ✅ File size: {sample_path.stat().st_size} bytes")
        else:
            print(f"   ⚠️  Sample dataset not found: {sample_path}")
        
        print("\n" + "=" * 50)
        print("🎉 Phase 2 Component Tests Completed Successfully!")
        print("\nNext Steps:")
        print("1. Start the Phase 2 backend: python start_phase2_backend.py")
        print("2. Test the API endpoints using the implementation guide")
        print("3. Run a sample simulation on the income dataset")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

async def test_sample_simulation():
    """Test running a sample simulation"""
    print("\n🚀 Testing Sample Simulation...")
    print("=" * 30)
    
    try:
        from api.services.simulation_service import simulation_service, SimulationConfig
        
        # Create test configuration
        config = SimulationConfig(
            model_type="regression",
            algorithm="random_forest",
            target_column="income",
            feature_columns=["age", "education", "experience"],
            protected_attributes=["gender"],
            test_size=0.3,
            random_state=42
        )
        
        print(f"Configuration: {config.model_type} - {config.algorithm}")
        print(f"Target: {config.target_column}")
        print(f"Features: {config.feature_columns}")
        print(f"Protected: {config.protected_attributes}")
        
        # Check if sample dataset exists
        dataset_path = "sample_datasets/sample_income_data.csv"
        if not Path(dataset_path).exists():
            print("   ⚠️  Sample dataset not found, skipping simulation test")
            return False
        
        print("\nRunning simulation...")
        result = await simulation_service.run_simulation(
            dataset_path=dataset_path,
            config=config
        )
        
        if result["success"]:
            print(f"   ✅ Simulation completed successfully!")
            print(f"   ✅ Simulation ID: {result['simulation_id']}")
            print(f"   ✅ Execution time: {result['results']['execution_time_ms']}ms")
            
            # Show performance metrics
            perf_metrics = result['results']['performance_metrics']
            print(f"   ✅ Performance: R²={perf_metrics.get('r2_score', 'N/A'):.3f}")
            
            # Show fairness metrics
            fairness_metrics = result['results']['fairness_metrics']
            if fairness_metrics:
                print(f"   ✅ Fairness analysis completed for {len(fairness_metrics)} protected attributes")
            
            return True
        else:
            print(f"   ❌ Simulation failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"   ❌ Simulation test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 FairMind Phase 2 Testing Suite")
    print("=" * 50)
    
    # Test components
    components_ok = await test_phase2_components()
    
    if components_ok:
        # Test sample simulation
        simulation_ok = await test_sample_simulation()
        
        if simulation_ok:
            print("\n🎉 ALL TESTS PASSED! Phase 2 is ready to use!")
        else:
            print("\n⚠️  Component tests passed, but simulation test failed")
    else:
        print("\n❌ Component tests failed. Please check the implementation.")
    
    print("\n" + "=" * 50)
    print("Testing complete!")

if __name__ == "__main__":
    asyncio.run(main())
