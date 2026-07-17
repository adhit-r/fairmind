# FairMind-E Paper Gate Evaluation

Fixture: `paper_gate_cases.json`

Claim under test: FairMind-E makes environmental release decisions machine-checkable from provenance, impact, mitigation, exceptions, and offset disclosure.

## Results

- Cases: 14
- Exact label accuracy: 14/14 (100.0%)
- Recommendation matches: 14/14
- Approval-blocking matches: 14/14

## Expected Recommendations

- `go`: 3
- `conditional_go`: 6
- `no_go`: 5

## Actual Recommendations

- `go`: 3
- `conditional_go`: 6
- `no_go`: 5

## Failures

None.

## Claim Boundary

This is a hand-labeled fixture evaluation for the paper method section. It is
not a workload-emissions measurement study, a regulatory compliance audit, or a
statistical benchmark over production systems.
