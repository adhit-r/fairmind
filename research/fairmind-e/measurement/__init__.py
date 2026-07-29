"""FairMind-E M5 measurement-study harness.

Unlike ``scripts/run_smoke.py`` (deterministic synthetic smoke artifacts),
this package executes real workloads on real hardware and derives energy and
carbon figures through three independent measurement methods:

- ``codecarbon``:   software power tracker      -> provenance ``tool_estimated``
- ``cloud_billing``: operator-supplied invoices -> provenance ``vendor_reported``
- ``manual_flop``:  analytic FLOP model         -> provenance ``manual``

The core study question: the same workload measured three ways yields
different provenance classes, therefore different confidence, and potentially
different gate decisions at identical true impact.

Honesty rules (hard requirements):

- No measurement is ever fabricated. When a dependency or data source is
  missing, the row is recorded with ``method_available=false`` and empty
  measurement fields, and the harness proceeds with what is real.
- Estimates carry ``provenance_class=manual``, tool outputs
  ``tool_estimated``, billing imports ``vendor_reported``.
- Dry runs are labeled ``run_mode=dry_run`` in every row.
"""
