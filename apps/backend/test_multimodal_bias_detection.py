#!/usr/bin/env python3
"""
Test script for Multimodal Bias Detection Service
Tests the new multimodal bias detection capabilities
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_multimodal_bias_detection():
    """Test the multimodal bias detection service"""
    try:
        logger.info("Testing Multimodal Bias Detection Service...")
        
        # Import the service
        from api.services.multimodal_bias_detection_service import (
            MultimodalBiasDetectionService,
            ModalityType,
            MultimodalBiasType
        )
        
        # Initialize the service
        service = MultimodalBiasDetectionService()
        logger.info("✓ Service initialized successfully")
        
        # Test 1: Check service configuration
        logger.info("\n1. Testing service configuration...")
        assert len(service.bias_detectors) == 3, "Should have 3 modality detectors"
        assert len(service.cross_modal_analyzers) == 4, "Should have 4 cross-modal analyzers"
        logger.info("✓ Service configuration is correct")
        
        # Test 2: Test image generation bias detection
        logger.info("\n2. Testing image generation bias detection...")
        mock_image_outputs = [
            {
                "text": "A professional in an office",
                "image_url": "https://example.com/image1.jpg",
                "metadata": {"generated_by": "test_model"},
                "protected_attributes": {"gender": "male", "race": "white"}
            },
            {
                "text": "A person cooking in a kitchen",
                "image_url": "https://example.com/image2.jpg",
                "metadata": {"generated_by": "test_model"},
                "protected_attributes": {"gender": "female", "race": "asian"}
            }
        ]
        
        image_results = await service.detect_image_generation_bias(mock_image_outputs)
        assert len(image_results) > 0, "Should return image bias results"
        assert all(hasattr(result, 'modality') for result in image_results), "Results should have modality"
        assert all(hasattr(result, 'bias_score') for result in image_results), "Results should have bias_score"
        logger.info(f"✓ Image bias detection returned {len(image_results)} results")
        
        # Test 3: Test audio generation bias detection
        logger.info("\n3. Testing audio generation bias detection...")
        mock_audio_outputs = [
            {
                "text": "Hello, how can I help you today?",
                "audio_url": "https://example.com/audio1.wav",
                "metadata": {"generated_by": "test_model"},
                "protected_attributes": {"gender": "male", "accent": "american"}
            },
            {
                "text": "Welcome to our service",
                "audio_url": "https://example.com/audio2.wav",
                "metadata": {"generated_by": "test_model"},
                "protected_attributes": {"gender": "female", "accent": "british"}
            }
        ]
        
        audio_results = await service.detect_audio_generation_bias(mock_audio_outputs)
        assert len(audio_results) > 0, "Should return audio bias results"
        assert all(hasattr(result, 'modality') for result in audio_results), "Results should have modality"
        assert all(hasattr(result, 'bias_score') for result in audio_results), "Results should have bias_score"
        logger.info(f"✓ Audio bias detection returned {len(audio_results)} results")
        
        # Test 4: Test video generation bias detection
        logger.info("\n4. Testing video generation bias detection...")
        mock_video_outputs = [
            {
                "text": "A person working at a computer",
                "video_url": "https://example.com/video1.mp4",
                "metadata": {"generated_by": "test_model"},
                "protected_attributes": {"gender": "male", "age": "middle"}
            },
            {
                "text": "Someone cooking dinner",
                "video_url": "https://example.com/video2.mp4",
                "metadata": {"generated_by": "test_model"},
                "protected_attributes": {"gender": "female", "age": "young"}
            }
        ]
        
        video_results = await service.detect_video_generation_bias(mock_video_outputs)
        assert len(video_results) > 0, "Should return video bias results"
        assert all(hasattr(result, 'modality') for result in video_results), "Results should have modality"
        assert all(hasattr(result, 'bias_score') for result in video_results), "Results should have bias_score"
        logger.info(f"✓ Video bias detection returned {len(video_results)} results")
        
        # Test 5: Test cross-modal bias detection
        logger.info("\n5. Testing cross-modal bias detection...")
        mock_cross_modal_outputs = [
            {
                "text": "A professional woman in business attire",
                "image_url": "https://example.com/image1.jpg",
                "audio_url": "https://example.com/audio1.wav",
                "metadata": {"generated_by": "test_model"},
                "protected_attributes": {"gender": "female", "profession": "business"}
            }
        ]
        
        modalities = [ModalityType.TEXT, ModalityType.IMAGE, ModalityType.AUDIO]
        cross_modal_results = await service.detect_cross_modal_bias(
            mock_cross_modal_outputs, modalities
        )
        assert len(cross_modal_results) > 0, "Should return cross-modal bias results"
        logger.info(f"✓ Cross-modal bias detection returned {len(cross_modal_results)} results")
        
        # Test 6: Test comprehensive multimodal analysis
        logger.info("\n6. Testing comprehensive multimodal analysis...")
        mock_comprehensive_outputs = [
            {
                "text": "A diverse group of professionals",
                "image_url": "https://example.com/image1.jpg",
                "audio_url": "https://example.com/audio1.wav",
                "video_url": "https://example.com/video1.mp4",
                "metadata": {"generated_by": "test_model"},
                "protected_attributes": {"diversity": "high"}
            }
        ]
        
        comprehensive_results = await service.comprehensive_multimodal_analysis(
            mock_comprehensive_outputs, modalities
        )
        assert "timestamp" in comprehensive_results, "Should have timestamp"
        assert "modalities" in comprehensive_results, "Should have modalities"
        assert "individual_modality_results" in comprehensive_results, "Should have individual results"
        assert "cross_modal_results" in comprehensive_results, "Should have cross-modal results"
        assert "overall_assessment" in comprehensive_results, "Should have overall assessment"
        assert "recommendations" in comprehensive_results, "Should have recommendations"
        logger.info("✓ Comprehensive multimodal analysis completed successfully")
        
        # Test 7: Test bias detector configuration
        logger.info("\n7. Testing bias detector configuration...")
        image_detectors = service.bias_detectors["image"]
        assert "demographic_detector" in image_detectors, "Should have demographic detector"
        assert "object_detector" in image_detectors, "Should have object detector"
        assert "style_detector" in image_detectors, "Should have style detector"
        
        audio_detectors = service.bias_detectors["audio"]
        assert "voice_detector" in audio_detectors, "Should have voice detector"
        assert "accent_detector" in audio_detectors, "Should have accent detector"
        assert "content_detector" in audio_detectors, "Should have content detector"
        
        video_detectors = service.bias_detectors["video"]
        assert "motion_detector" in video_detectors, "Should have motion detector"
        assert "temporal_detector" in video_detectors, "Should have temporal detector"
        assert "scene_detector" in video_detectors, "Should have scene detector"
        logger.info("✓ Bias detector configuration is correct")
        
        # Test 8: Test cross-modal analyzer configuration
        logger.info("\n8. Testing cross-modal analyzer configuration...")
        cross_modal_analyzers = service.cross_modal_analyzers
        assert "text_image" in cross_modal_analyzers, "Should have text-image analyzer"
        assert "text_audio" in cross_modal_analyzers, "Should have text-audio analyzer"
        assert "image_audio" in cross_modal_analyzers, "Should have image-audio analyzer"
        assert "text_video" in cross_modal_analyzers, "Should have text-video analyzer"
        logger.info("✓ Cross-modal analyzer configuration is correct")
        
        # Test 9: Test result structure
        logger.info("\n9. Testing result structure...")
        sample_result = image_results[0]
        assert hasattr(sample_result, 'modality'), "Result should have modality"
        assert hasattr(sample_result, 'bias_type'), "Result should have bias_type"
        assert hasattr(sample_result, 'bias_score'), "Result should have bias_score"
        assert hasattr(sample_result, 'confidence'), "Result should have confidence"
        assert hasattr(sample_result, 'is_biased'), "Result should have is_biased"
        assert hasattr(sample_result, 'details'), "Result should have details"
        assert hasattr(sample_result, 'recommendations'), "Result should have recommendations"
        assert hasattr(sample_result, 'timestamp'), "Result should have timestamp"
        logger.info("✓ Result structure is correct")
        
        # Test 10: Test overall assessment generation
        logger.info("\n10. Testing overall assessment generation...")
        assessment = comprehensive_results["overall_assessment"]
        assert "overall_bias_score" in assessment, "Should have overall bias score"
        assert "biased_modalities" in assessment, "Should have biased modalities"
        assert "cross_modal_bias_detected" in assessment, "Should have cross-modal bias flag"
        assert "risk_level" in assessment, "Should have risk level"
        logger.info("✓ Overall assessment generation is correct")
        
        logger.info("\n🎉 All multimodal bias detection tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    logger.info("=" * 60)
    logger.info("MULTIMODAL BIAS DETECTION SERVICE TEST")
    logger.info("=" * 60)
    
    success = await test_multimodal_bias_detection()
    
    logger.info("\n" + "=" * 60)
    if success:
        logger.info("✅ ALL TESTS PASSED - Multimodal bias detection is working correctly!")
    else:
        logger.info("❌ TESTS FAILED - Please check the implementation")
    logger.info("=" * 60)
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
