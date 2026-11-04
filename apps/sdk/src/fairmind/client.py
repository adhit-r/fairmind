"""HTTP client for the FairMind API. Mirrors the conventions of the fairmind CLI."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import httpx

from . import __version__
from .types import Attestation, AttestableCheck, ClauseMap, FairnessRun, Gate, MonitoringRun, System

GOV = "/api/v1/ai-governance"
DEFAULT_API_URL = "http://localhost:8010"

# legacy framework ids -> catalogue keys, as accepted by the report request
_FRAMEWORK_ALIASES = {"eu_ai_act": "EUAIA", "iso_42001": "ISO42001", "nist_ai_rmf": "NISTRMF", "india_ai": "INDAI"}

PathLike = Union[str, "os.PathLike[str]"]


class FairMindError(Exception):
    """A failed call. `status_code` is None when the server could not be reached."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __str__(self) -> str:
        return f"{self.status_code}: {self.message}" if self.status_code else self.message


def _split(value: Union[str, Sequence[str]]) -> str:
    return value if isinstance(value, str) else ",".join(value)


class FairMind:
    """`FairMind(api_url=None, api_key=None)`; FAIRMIND_API_URL and FAIRMIND_API_KEY are read when omitted."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        *,
        timeout: Union[float, httpx.Timeout] = httpx.Timeout(180.0, connect=10.0),
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self.api_url = (api_url or os.environ.get("FAIRMIND_API_URL") or DEFAULT_API_URL).rstrip("/")
        key = api_key or os.environ.get("FAIRMIND_API_KEY") or ""
        headers = {"Accept": "application/json", "User-Agent": f"fairmind-sdk/{__version__}"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        self._http = httpx.Client(base_url=self.api_url, headers=headers, timeout=timeout, transport=transport)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "FairMind":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # -- transport -----------------------------------------------------------

    def _call(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = self._http.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise FairMindError(f"Could not reach FairMind at {self.api_url}: {exc}") from exc
        code = response.status_code
        if code == 401:
            raise FairMindError("Not signed in. Set FAIRMIND_API_KEY to a key from POST /api/v1/auth/api-keys.", code)
        if code >= 400:
            try:
                body = response.json()
                detail = body.get("detail") or body.get("message") or response.text
            except (ValueError, AttributeError):
                detail = response.text
            if code == 404:
                detail = f"Not found: {path}. Check the system id and that your key belongs to its organisation. {detail}"
            raise FairMindError(f"{method} {path} failed: {detail}", code)
        try:
            return response.json()
        except ValueError as exc:
            raise FairMindError(f"{method} {path} returned something that is not JSON", code) from exc

    def _upload(self, path: str, csv_path: PathLike, data: Dict[str, str]) -> Any:
        p = Path(csv_path)
        if not p.is_file():
            raise FairMindError(f"No such file: {p}")
        with p.open("rb") as handle:
            return self._call("POST", path, data=data, files={"file": (p.name, handle, "text/csv")})

    # -- reads ---------------------------------------------------------------

    def systems(self) -> List[System]:
        return self._call("GET", f"{GOV}/systems")

    def gate(self, system_id: str) -> Gate:
        return self._call("GET", f"{GOV}/systems/{system_id}/gate")

    def clause_map(self, system_id: str, frameworks: Optional[Sequence[str]] = None) -> ClauseMap:
        """The gate read per framework clause. `frameworks` filters client-side by catalogue key (EUAIA, ISO42001, ...)."""
        result = self._call("GET", f"{GOV}/systems/{system_id}/clause-map")
        if frameworks:
            wanted = {_FRAMEWORK_ALIASES.get(f.lower(), f).upper() for f in frameworks}
            result["frameworks"] = [f for f in result["frameworks"] if f["key"].upper() in wanted]
        return result

    def seals(self, system_id: str) -> List[Dict[str, Any]]:
        return self._call("GET", f"{GOV}/systems/{system_id}/seals")

    def fairness_runs(self, system_id: str) -> List[Dict[str, Any]]:
        return self._call("GET", f"{GOV}/systems/{system_id}/fairness-runs")

    def monitoring_runs(self, system_id: str) -> List[Dict[str, Any]]:
        return self._call("GET", f"{GOV}/systems/{system_id}/monitoring-runs")

    # -- writes --------------------------------------------------------------

    def inspect_csv(self, system_id: str, path: PathLike) -> Dict[str, Any]:
        """Columns of a CSV with sample values and a suggested outcome/prediction/score/attributes mapping."""
        return self._upload(f"{GOV}/systems/{system_id}/fairness-runs/inspect", path, {})

    def run_fairness(
        self,
        system_id: str,
        path: PathLike,
        *,
        outcome: str,
        attributes: Union[str, Sequence[str]],
        prediction: Optional[str] = None,
        score: Optional[str] = None,
        favorable_label: Optional[str] = None,
    ) -> FairnessRun:
        if not prediction and not score:
            raise FairMindError("Give prediction (a 0/1 column) or score (a 0 to 1 column)")
        data = {"outcome": outcome, "attributes": _split(attributes)}
        for key, value in (("prediction", prediction), ("score", score), ("favorable_label", favorable_label)):
            if value:
                data[key] = value
        return self._upload(f"{GOV}/systems/{system_id}/fairness-runs", path, data)

    def run_monitoring(
        self,
        system_id: str,
        path: PathLike,
        *,
        attributes: Union[str, Sequence[str]],
        prediction: Optional[str] = None,
        score: Optional[str] = None,
        favorable_label: Optional[str] = None,
    ) -> MonitoringRun:
        if not prediction and not score:
            raise FairMindError("Give prediction (a 0/1 column) or score (a 0 to 1 column)")
        data = {"attributes": _split(attributes)}
        for key, value in (("prediction", prediction), ("score", score), ("favorable_label", favorable_label)):
            if value:
                data[key] = value
        return self._upload(f"{GOV}/systems/{system_id}/monitoring-runs", path, data)

    def attest(self, system_id: str, check: AttestableCheck, statement: str, reference: Optional[str] = None) -> Attestation:
        """Record that a person states a gate check is satisfied. Manual provenance: it attests, it never proves."""
        body: Dict[str, Any] = {"check": check, "statement": statement}
        if reference:
            body["reference"] = reference
        return self._call("POST", f"{GOV}/systems/{system_id}/attestations", json=body)
