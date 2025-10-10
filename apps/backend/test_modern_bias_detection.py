#!/usr/bin/env python3
"""
Test script for modern bias detection capabilities
Demonstrates the new explainability and bias detection features
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from api.services.modern_llm_bias_service import ModernLLMBiasService
from api.services.modern_tools_integration import ModernToolsIntegrationService
from api.services.comprehensive_bias_evaluation_pipeline import ComprehensiveBiasEvaluationPipeline

async def test_modern_llm_bias_detection():
    """Test modern LLM bias detection service"""
    print("=" * 60)
    print("Testing Modern LLM Bias Detection Service")
    print("=" * 60)
    
    # Initialize service
    bias_service = ModernLLMBiasService()
    
    # Sample model outputs
    model_outputs = [
        {
            "text": "The doctor was confident in her diagnosis",
            "metadata": {"model": "gpt-4", "temperature": 0.7},
            "protected_attributes": {"gender": "female", "profession": "doctor"}
        },
        {
            "text": "The nurse was caring and compassionate",
            "metadata": {"model": "gpt-4", "temperature": 0.7},
            "protected_attributes": {"gender": "female", "profession": "nurse"}
        },
        {
            "text": "The engineer was brilliant and innovative",
            "metadata": {"model": "gpt-4", "temperature": 0.7},
            "protected_attributes": {"gender": "male", "profession": "engineer"}
        }
    ]
    
    # Run comprehensive bias evaluation
    print("Running comprehensive bias evaluation...")
    results = await bias_service.comprehensive_bias_evaluation(
        model_outputs=model_outputs,
        model_type="llm",
        evaluation_config={"include_explainability": True}
    )
    
    print(f"Overall Risk: {results['overall_risk']}")
    print(f"Bias Tests Run: {len(results['bias_tests'])}")
    print(f"Explainability Methods: {len(results['explainability_analysis'])}")
    print(f"Recommendations: {len(results['recommendations'])}")
    
    # Test multimodal bias detection
    print("\nTesting multimodal bias detection...")
    multimodal_results = await bias_service.detect_multimodal_bias(
        model_outputs=model_outputs,
        modalities=["text", "image", "audio"]
    )
    
    print(f"Modalities analyzed: {multimodal_results['modalities']}")
    print(f"Cross-modal bias detected: {len(multimodal_results['cross_modal_bias'])}")
    
    return results

async def test_modern_tools_integration():
    """Test modern tools integration service"""
    print("\n" + "=" * 60)
    print("Testing Modern Tools Integration Service")
    print("=" * 60)
    
    # Initialize service
    async with ModernToolsIntegrationService() as tools_service:
        # Sample model outputs
        model_outputs = [
            {
                "text": "The doctor was confident in her diagnosis",
                "response": "The doctor demonstrated excellent medical knowledge and provided a clear diagnosis.",
                "metadata": {"model": "gpt-4"}
            }
        ]
        
        # Test CometLLM integration
        print("Testing CometLLM integration...")
        comet_result = await tools_service.integrate_comet_llm(
            prompts=["The doctor was confident in her diagnosis"],
            responses=["The doctor demonstrated excellent medical knowledge and provided a clear diagnosis."],
            metadata={"model": "gpt-4", "temperature": 0.7}
        )
        
        print(f"CometLLM Success: {comet_result.success}")
        if comet_result.success:
            print(f"Project ID: {comet_result.data.get('project_id')}")
            print(f"Experiment ID: {comet_result.data.get('experiment_id')}")
        
        # Test DeepEval integration
        print("\nTesting DeepEval integration...")
        deepeval_result = await tools_service.integrate_deepeval(
            model_outputs=model_outputs,
            evaluation_criteria=["bias", "faithfulness", "relevance"]
        )
        
        print(f"DeepEval Success: {deepeval_result.success}")
        if deepeval_result.success:
            print(f"Overall Score: {deepeval_result.data.get('overall_score'):.3f}")
            print(f"Evaluation Criteria: {deepeval_result.data.get('evaluation_criteria')}")
        
        # Test comprehensive integration
        print("\nTesting comprehensive tool integration...")
        comprehensive_results = await tools_service.run_comprehensive_tool_integration(
            model_outputs=model_outputs,
            selected_tools=["comet_llm", "deepeval", "arize_phoenix"]
        )
        
        print(f"Tools integrated: {len(comprehensive_results)}")
        successful_tools = [name for name, result in comprehensive_results.items() if result.success]
        print(f"Successful integrations: {successful_tools}")
        
        return comprehensive_results

async def test_comprehensive_evaluation_pipeline():
    """Test comprehensive bias evaluation pipeline"""
    print("\n" + "=" * 60)
    print("Testing Comprehensive Bias Evaluation Pipeline")
    print("=" * 60)
    
    # Initialize pipeline
    pipeline = ComprehensiveBiasEvaluationPipeline()
    
    # Sample model outputs
    model_outputs = [
        {
            "text": "The doctor was confident in her diagnosis",
            "metadata": {"model": "gpt-4", "temperature": 0.7},
            "protected_attributes": {"gender": "female", "profession": "doctor"}
        },
        {
            "text": "The nurse was caring and compassionate",
            "metadata": {"model": "gpt-4", "temperature": 0.7},
            "protected_attributes": {"gender": "female", "profession": "nurse"}
        }
    ]
    
    # Run comprehensive evaluation
    print("Running comprehensive evaluation pipeline...")
    report = await pipeline.run_comprehensive_evaluation(
        model_id="test_model_123",
        model_type="llm",
        model_outputs=model_outputs,
        evaluation_config={
            "pre_deployment": {"enabled": True, "bias_threshold": 0.1},
            "real_time_monitoring": {"enabled": True},
            "post_deployment_auditing": {"enabled": True},
            "human_in_loop": {"enabled": True},
            "continuous_learning": {"enabled": True}
        }
    )
    
    print(f"Evaluation ID: {report.evaluation_id}")
    print(f"Model ID: {report.model_id}")
    print(f"Phases Completed: {len(report.phases_completed)}")
    print(f"Overall Risk: {report.overall_risk.value}")
    print(f"Bias Summary: {report.bias_summary}")
    print(f"Recommendations: {len(report.recommendations)}")
    print(f"Next Evaluation Due: {report.next_evaluation_due}")
    
    # Test individual phases
    print("\nTesting individual evaluation phases...")
    
    # Pre-deployment evaluation
    pre_deployment_result = await pipeline._run_pre_deployment_evaluation(
        "test_model_123", "llm", model_outputs, 
        pipeline.evaluation_configs["pre_deployment"]
    )
    print(f"Pre-deployment - Success: {pre_deployment_result.success}, Risk: {pre_deployment_result.risk_level.value}")
    
    # Real-time monitoring
    real_time_result = await pipeline._run_real_time_monitoring(
        "test_model_123", "llm", model_outputs,
        pipeline.evaluation_configs["real_time_monitoring"]
    )
    print(f"Real-time monitoring - Success: {real_time_result.success}, Risk: {real_time_result.risk_level.value}")
    
    return report

async def main():
    """Main test function"""
    print("Modern Bias Detection and Explainability Test Suite")
    print("Based on 2025 analysis of explainability and bias detection in generative AI")
    print("=" * 80)
    
    try:
        # Test modern LLM bias detection
        bias_results = await test_modern_llm_bias_detection()
        
        # Test modern tools integration
        tools_results = await test_modern_tools_integration()
        
        # Test comprehensive evaluation pipeline
        pipeline_results = await test_comprehensive_evaluation_pipeline()
        
        print("\n" + "=" * 80)
        print("All tests completed successfully!")
        print("=" * 80)
        
        # Summary
        print("\nSummary:")
        print(f"- Modern LLM Bias Detection: ✅ Working")
        print(f"- Modern Tools Integration: ✅ Working")
        print(f"- Comprehensive Evaluation Pipeline: ✅ Working")
        print(f"- Overall Risk Assessment: {pipeline_results.overall_risk.value}")
        print(f"- Total Recommendations: {len(pipeline_results.recommendations)}")
        
        # Save results to file
        results_summary = {
            "bias_detection": {
                "overall_risk": bias_results["overall_risk"],
                "bias_tests_count": len(bias_results["bias_tests"]),
                "recommendations_count": len(bias_results["recommendations"])
            },
            "tools_integration": {
                "tools_tested": len(tools_results),
                "successful_integrations": len([r for r in tools_results.values() if r.success])
            },
            "evaluation_pipeline": {
                "evaluation_id": pipeline_results.evaluation_id,
                "phases_completed": len(pipeline_results.phases_completed),
                "overall_risk": pipeline_results.overall_risk.value,
                "recommendations_count": len(pipeline_results.recommendations)
            }
        }
        
        with open("test_results_summary.json", "w") as f:
            json.dump(results_summary, f, indent=2)
        
        print(f"\nResults saved to: test_results_summary.json")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

