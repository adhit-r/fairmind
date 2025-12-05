import logging
from typing import Dict, Any, List, Optional
import os
import sys

# Add the parent of the vendored directory to the python path so we can import bias_bench as a package
VENDOR_DIR = os.path.join(os.path.dirname(__file__), "bias_bench")
sys.path.append(os.path.dirname(VENDOR_DIR))

import torch
from transformers import AutoModelForMaskedLM, AutoTokenizer, AutoModelForCausalLM

try:
    # Attempt to import from vendored code
    from bias_bench.benchmark.stereoset import StereoSetRunner
    from bias_bench.benchmark.crows import CrowSPairsRunner
    from bias_bench.benchmark.seat import SEATRunner
except ImportError as e:
    logging.warning(f"Failed to import bias_bench dependencies: {e}. Bias benchmarking may not work.")

logger = logging.getLogger(__name__)

class BiasBenchService:
    def __init__(self):
        self.supported_benchmarks = ["stereoset", "crows", "seat"]
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    async def evaluate_model(self, model_name_or_path: str, benchmark_name: str) -> Dict[str, Any]:
        """
        Evaluate a model using a specific benchmark from bias-bench.
        """
        benchmark_name = benchmark_name.lower()
        if benchmark_name not in self.supported_benchmarks:
            raise ValueError(f"Unsupported benchmark: {benchmark_name}. Supported: {self.supported_benchmarks}")

        logger.info(f"Starting {benchmark_name} evaluation for {model_name_or_path}")

        try:
            # Load model and tokenizer
            # For now, assuming causal LM for generative tasks, but bias-bench often defaults to masked LM
            # We'll try to detect or default to CausalLM for modern LLMs
            is_generative = True
            try:
                tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
                model = AutoModelForCausalLM.from_pretrained(model_name_or_path)
            except Exception:
                # Fallback to MaskedLM if CausalLM fails (e.g. BERT)
                logger.info(f"Could not load as CausalLM, trying MaskedLM for {model_name_or_path}")
                tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
                model = AutoModelForMaskedLM.from_pretrained(model_name_or_path)
                is_generative = False
            
            model.to(self.device)

            if benchmark_name == "stereoset":
                # StereoSetRunner requires input_file. We need to point to the data in the vendored repo.
                data_path = os.path.join(os.path.dirname(VENDOR_DIR), "bias_bench", "data", "stereoset", "test.json")
                # Note: The vendored repo structure might differ, we might need to adjust data path
                # For now, let's assume standard location or mock it if file missing
                
                runner = StereoSetRunner(
                    intrasentence_model=model,
                    tokenizer=tokenizer,
                    model_name_or_path=model_name_or_path,
                    is_generative=is_generative
                )
                results = runner()
                return results
            
            elif benchmark_name == "crows":
                runner = CrowSPairsRunner(
                    model=model,
                    tokenizer=tokenizer,
                    is_generative=is_generative
                )
                results = runner()
                return results

            elif benchmark_name == "seat":
                # SEAT might require different arguments
                runner = SEATRunner(
                    model=model,
                    tokenizer=tokenizer
                )
                results = runner()
                return results

        except Exception as e:
            logger.error(f"Error running {benchmark_name} on {model_name_or_path}: {e}")
            raise e

    def get_supported_benchmarks(self) -> List[str]:
        return self.supported_benchmarks

bias_bench_service = BiasBenchService()
