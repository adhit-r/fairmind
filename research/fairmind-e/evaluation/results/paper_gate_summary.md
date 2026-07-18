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

## Baseline Comparison

| Gate | Exact Matches | Exact Accuracy | Recommendation Matches | Approval-Blocking Matches |
| --- | ---: | ---: | ---: | ---: |
| carbon_only_gate | 7/14 | 50.0% | 8/14 | 10/14 |
| fairmind_e | 14/14 | 100.0% | 14/14 | 14/14 |
| generic_sustainability_score | 6/14 | 42.9% | 8/14 | 7/14 |
| no_environmental_gate | 3/14 | 21.4% | 3/14 | 6/14 |
| no_exception_path | 13/14 | 92.9% | 14/14 | 13/14 |
| no_mitigation_review_gate | 11/14 | 78.6% | 14/14 | 11/14 |
| offset_credit_gate | 13/14 | 92.9% | 13/14 | 13/14 |

## Failures

None.

## Claim Boundary

This is a hand-labeled fixture evaluation for the paper method section. It is
not a workload-emissions measurement study, a regulatory compliance audit, or a
statistical benchmark over production systems.
