import asyncio
import logging

import pytest

try:
    from domain.bias.services.bias_bench_service import bias_bench_service
except ModuleNotFoundError as exc:
    pytest.skip(f"bias bench dependencies unavailable: {exc}", allow_module_level=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_bias_bench():
    logger.info("Testing BiasBenchService integration...")
    
    benchmarks = bias_bench_service.get_supported_benchmarks()
    logger.info(f"Supported benchmarks: {benchmarks}")
    
    # We won't run a full evaluation here as it requires a model and might take time/memory
    # Just checking if imports worked without crashing is a good first step
    
    logger.info("BiasBenchService imported successfully.")

if __name__ == "__main__":
    asyncio.run(test_bias_bench())
