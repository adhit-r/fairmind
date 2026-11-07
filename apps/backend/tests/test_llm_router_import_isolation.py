"""Importing the LLM router must not load the compliance automation chain.

llm.py is imported by required routers, so anything it loads at import time can
stop the API from starting. The compliance chain builds a scheduler and creates
directories on import; it belongs only to the optional compliance routers.
"""

import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]


def test_llm_router_import_does_not_load_compliance_automation():
    probe = (
        "import sys, src.api.routers.llm; "
        "print('src.domain.compliance.services.compliance_automation_service' in sys.modules)"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe], cwd=BACKEND, env=os.environ.copy(),
        capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().splitlines()[-1] == "False"
