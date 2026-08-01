# Evidence Passport V2 signing contract

Status: internal contract, revision 1

Schema: `apps/backend/src/domain/assurance/evidence-passport-v2.schema.json`

Domain implementation: `apps/backend/src/domain/assurance/evidence_passport_v2.py`

## Claim boundary

An Evidence Passport V2 is a signed statement from one evaluator about one
suite execution. Its fixed claim boundary is
`supporting_evidence_only`.

A structurally valid or cryptographically authentic Passport is not admitted
evidence, an accepted framework mapping, a governance verdict, a compliance
decision, a certification, or a FairMind verification mark. Trust-policy
selection, key state, replay prevention, expiry at admission time, reviewer
acceptance, and governance decisions remain separate application concerns.

The initial signed kernel accepts only two evaluator sources:

- `fairmind_worker`
- `external_provider`

The evaluator `sourceType` must equal the bound execution `deliveryMode`.
`imported_report` envelopes may be derived for other workflows, but an imported
report cannot normalize as a signed Passport V2. Imported reports remain
unverified, human-review-only inputs under the separate admission workflow.

## One Passport, one suite execution

Every Passport binds exactly one suite execution from one immutable
`ExecutionEnvelopeV2`. The server derives the binding with
`expected_execution_binding_v2(envelope, suiteExecutionId)`; an adapter does not
construct the expected binding.

Derivation performs these steps:

1. Require the exact closed `ExecutionEnvelopeV2` field set.
2. Rebuild the envelope through the public `build_execution_envelope_v2`
   contract using the supplied server fields.
3. Require the rebuilt value to equal the supplied value.
4. calculate the envelope hash over the rebuilt RFC 8785 bytes.
5. Require the requested `suiteExecutionId` to occur exactly once.
6. Copy only the normative binding fields into a new isolated object.

The execution binding contains:

| Scope | Bound values |
| --- | --- |
| Tenant | organization, workspace, and system IDs |
| Execution | run ID, envelope ID and hash, nonce |
| Plan | plan ID and content hash |
| Target | target-version ID, subject digest, manifest digest |
| Suite | suite-execution ID, suite-version ID, manifest digest, configuration hash |
| Runtime | lifecycle phase, execution depth, enforcement mode, delivery mode |
| Trust | trust-policy version ID and policy hash |

The Passport repeats organization, workspace, and system IDs at its top level.
Those values must exactly equal the same values in `executionBinding`.

## Closed document

The required top-level fields are:

```text
schemaVersion             "2.0.0"
passportId
passportRevision          1
claimBoundary             "supporting_evidence_only"
organizationId
workspaceId
systemId
executionBinding
evaluator
result
artifacts
limitations
capturedAt
expiresAt
contentHash
signature
```

Unknown fields are rejected at the top level and at every protocol object
boundary. The result `summary` is the only evaluator-defined JSON object. It is
bounded and receives defense-in-depth screening for known sensitive keys and
recognized unsafe public values. That heuristic screening is not comprehensive
DLP and cannot prove that arbitrary prose contains no personal or private data.
Before admission wiring, each evaluator must be constrained by its versioned
result-contract schema, with adapter normalization and artifact quarantine as
the authoritative data boundary.

Artifacts are references by identity and digest only. Each artifact has exactly
`artifactId`, `role`, `sha256`, `mediaType`, and `sizeBytes`. URLs, paths,
credentials, inline content, and raw evaluator outputs are not part of this
contract. Artifact IDs must be unique and a Passport may contain no more than
50 artifact references.

The contract accepts exactly one singular `signature`. Public keys, private
keys, JWKs, certificate chains, and multiple-signature arrays are excluded.
Key material is resolved by the trust service using `issuerId` and `keyId`.

## Content hash

`contentHash` is lowercase hexadecimal SHA-256 over RFC 8785 canonical bytes of
the whole Passport after excluding exactly these two top-level fields:

- `contentHash`
- `signature`

No other field is excluded. Tenant and execution scope, evaluator identity,
normalized result, artifact digests, limitations, capture time, and expiry are
therefore all hash-significant.

Conceptually:

```text
contentProjection = passport - {contentHash, signature}
contentHash = hex(SHA-256(RFC8785(contentProjection)))
```

The implementation reuses `evaluation_v2.canonical_json_bytes` and
`evaluation_v2.canonical_sha256`. Sorted-key JSON is not an acceptable
substitute for RFC 8785, and the Passport module does not implement a second
canonicalizer.

## Ed25519 signing input

The only supported algorithm in revision 1 is `Ed25519`. The signature value is
the canonical unpadded base64url encoding of exactly 64 signature bytes.

The signing projection is exactly:

```json
{
  "schemaVersion": "fairmind/evidence-signature/2.0.0",
  "contentHash": "<passport contentHash>",
  "protected": {
    "algorithm": "Ed25519",
    "issuerId": "<signature issuerId>",
    "keyId": "<signature keyId>",
    "signedAt": "<canonical UTC timestamp>"
  }
}
```

The bytes passed to Ed25519 are `RFC8785(signingProjection)`. The signature
value itself and all key material are excluded. The signature issuer must equal
the evaluator issuer.

## Result semantics

`technicalStatus` describes evaluator execution. `evidenceResultStatus`
describes what the evaluator observed about the target. They are deliberately
separate axes.

A successful evaluator may report failed target evidence:

```text
technicalStatus = succeeded
evidenceResultStatus = failed
```

This is a valid and important state. Conversely, a failed, timed-out, or
cancelled evaluator cannot report `passed`, `passed_with_limitations`, or
`failed` target evidence. Evaluator failure must remain `error`, `unavailable`,
`insufficient_data`, or `unknown`. No execution failure is translated into a
passing result. A `passed_with_limitations` result must include at least one
limitation, and a non-successful evaluator execution must include a non-empty,
bounded diagnostic summary.

The Passport does not contain admission state, review state, freshness state,
or governance verdict. Those axes are produced only by downstream workflows.

## Time and chronology

`capturedAt`, `signature.signedAt`, and `expiresAt` use the canonical Python
RFC 3339 UTC form ending in `+00:00`. The `Z` spelling, non-UTC offsets, naive
timestamps, and non-canonical equivalent encodings are rejected.

Chronology must satisfy:

```text
capturedAt <= signedAt <= expiresAt
capturedAt < expiresAt
```

Whether the Passport is expired at the time of admission remains a separate
admission decision. Normalization verifies the signed chronology, not current
wall-clock freshness.

## Parser and safety limits

The byte parser fails closed on malformed UTF-8, duplicate object names,
non-finite numbers, values outside the I-JSON numeric domain, non-object roots,
and equivalent unsafe serializations. Direct normalization applies the same
canonical-domain, depth, and size protections.

Revision 1 limits are:

| Boundary | Limit |
| --- | ---: |
| Raw or canonical Passport | 1 MiB |
| Result summary | 64 KiB canonical |
| Limitations | 8 KiB canonical |
| JSON depth | 32 |
| JSON values | 50,000 |
| Artifact references | 50 |

Known secret, credential, authorization, private-key, chain-of-thought, raw
prompt, and raw-output fields, plus recognized secret-like values, are rejected
as defense in depth. This is deliberately not described as exhaustive PII or
DLP detection. Validation errors use bounded messages and never reflect
submitted values.

## Verification sequence

A caller performing authenticity assessment should:

1. Parse and normalize the Passport.
2. Compare its tenant and execution binding with the server-derived expected
   binding.
3. Recalculate and constant-time compare `contentHash`.
4. Resolve the immutable trust-policy version and exact issuer/key record.
5. Check algorithm, issuer, key validity, revocation, chronology, and freshness.
6. Verify the Ed25519 signature over
   `evidence_passport_v2_signature_bytes(passport)`.
7. Apply replay, supersession, admission, and reviewer policy separately.

Passing these steps establishes bounded authenticity for a supporting-evidence
statement. It does not establish that the evidence is sufficient, accepted,
current for a decision, or compliant with a governance framework.

The current authenticity service accepts `ExpectedServerBinding` and
`TrustedSigningKey` as trusted caller capabilities. It does not prove their
provenance. Admission wiring must derive the former from the stored server
envelope and resolve the latter under the bound organization, trust-policy
version, source, and suite restrictions. It must also add replay and
supersession checks. The service currently permits no future clock skew and
treats `expiresAt <= now` as expired; any later skew allowance must come from an
immutable trust-policy version and receive boundary tests.
