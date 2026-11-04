"""Engines that read datasets: drift, representativeness, completeness, duplicates, personal data, poisoning, labels."""

import io
import json
import re
import warnings
from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import sparse, stats
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import cohen_kappa_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.neighbors import NearestNeighbors

from .common import Engine, EngineError, Param, Slot, columns, number, read_csv, result, split
from .detectors import INSTRUCTIONS, PERSONAL, SECRETS, mask, scan

EPS = 1e-4
MIN_ROWS = 20


def _is_text(series: pd.Series) -> bool:
    values = series.dropna().astype(str)
    textual = pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)
    return textual and len(values) > 0 and (values.str.len().mean() > 30 or values.nunique() > 0.5 * len(values) > 50)


def _psi(expected: np.ndarray, actual: np.ndarray) -> float:
    e = np.clip(expected / max(expected.sum(), 1), EPS, None)
    a = np.clip(actual / max(actual.sum(), 1), EPS, None)
    return float(np.sum((a - e) * np.log(a / e)))


def _feature_drift(ref: pd.Series, cur: pd.Series) -> Dict[str, Any]:
    if pd.api.types.is_numeric_dtype(ref) and pd.api.types.is_numeric_dtype(cur):
        r, c = ref.dropna().to_numpy(float), cur.dropna().to_numpy(float)
        edges = np.unique(np.quantile(r, np.linspace(0, 1, 11)))
        edges = np.concatenate(([-np.inf], edges[1:-1], [np.inf])) if len(edges) > 2 else np.array([-np.inf, np.median(r), np.inf])
        ks = stats.ks_2samp(r, c)
        return {"type": "numeric", "psi": _psi(np.histogram(r, edges)[0], np.histogram(c, edges)[0]),
                "ks": float(ks.statistic), "pValue": float(ks.pvalue)}
    r, c = ref.astype(str).fillna(""), cur.astype(str).fillna("")
    cats = sorted(set(r) | set(c))
    return {"type": "categorical", "psi": _psi(r.value_counts().reindex(cats, fill_value=0).to_numpy(float),
                                               c.value_counts().reindex(cats, fill_value=0).to_numpy(float)), "ks": None, "pValue": None}


def _matrix(ref: pd.DataFrame, cur: pd.DataFrame, features: List[str]):
    both = pd.concat([ref[features], cur[features]], ignore_index=True)
    parts = []
    for f in features:
        col = both[f]
        if pd.api.types.is_numeric_dtype(col):
            v = col.astype(float).fillna(col.astype(float).median())
            sd = v.std() or 1.0
            parts.append(sparse.csr_matrix(((v - v.mean()) / sd).to_numpy()[:, None]))
        elif _is_text(col):
            parts.append(TfidfVectorizer(max_features=2000, ngram_range=(1, 2), min_df=1).fit_transform(col.fillna("").astype(str)))
        else:
            top = col.astype(str).value_counts().index[:50]
            parts.append(sparse.csr_matrix(pd.get_dummies(col.astype(str).where(col.astype(str).isin(top), "other")).to_numpy(float)))
    return sparse.hstack(parts).tocsr()


def _sample_scores(ref: pd.DataFrame, cur: pd.DataFrame, features: List[str]) -> Tuple[np.ndarray, np.ndarray]:
    """Density ratio p_ref(x) / p_cur(x) per current row, from a classifier that tells the two sets apart.

    Probabilities are out-of-fold, so no row is scored by a model that saw it. A ratio near 1 means
    the row looks like the reference; near 0 means the reference has nothing like it.
    """
    X = _matrix(ref, cur, features)
    y = np.r_[np.zeros(len(ref)), np.ones(len(cur))]
    folds = StratifiedKFold(n_splits=min(5, len(ref), len(cur)), shuffle=True, random_state=0)
    p = cross_val_predict(LogisticRegression(max_iter=2000, C=1.0), X, y, cv=folds, method="predict_proba")[len(ref):, 1]
    p = np.clip(p, 1e-6, 1 - 1e-6)
    ratio = (1 - p) / p * (len(cur) / len(ref))
    score = np.where(ratio >= 0.5, 1.0, np.where(ratio >= 0.1, 0.5, 0.0))
    return ratio, score


def _cell(value: Any) -> Any:
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return round(float(value), 4)
    return str(value)[:120]


def data_drift(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    ref, cur = read_csv(files["reference"], "The reference set"), read_csv(files["current"], "The current set")
    wanted = split(params.get("features"))
    skip = set(split(params.get("ignore")))
    features = wanted or [c for c in ref.columns if c in cur.columns and c not in skip]
    columns(ref, features, "The reference set")
    columns(cur, features, "The current set")
    if not features:
        raise EngineError("The two sets share no columns to compare")
    psi_limit = number(params, "psi_limit", 0.2)
    min_share = number(params, "min_in_distribution", 0.9)

    rows, tabular = [], []
    for f in features:
        if _is_text(ref[f]):
            rows.append({"kind": "feature", "feature": f, "type": "text", "psi": None, "ks": None, "pValue": None, "drifted": None})
            continue
        d = _feature_drift(ref[f], cur[f])
        d["psi"] = round(d["psi"], 4)
        rows.append({"kind": "feature", "feature": f, **d, "drifted": d["psi"] >= psi_limit})
        tabular.append(d["psi"])

    metrics: Dict[str, Any] = {"referenceRows": len(ref), "currentRows": len(cur), "features": len(features),
                               "driftedFeatures": sum(1 for r in rows if r["drifted"]), "maxPsi": round(max(tabular), 4) if tabular else None}
    if len(ref) < MIN_ROWS or len(cur) < MIN_ROWS:
        return result("insufficient", f"Each set needs at least {MIN_ROWS} rows to measure drift; got {len(ref)} and {len(cur)}.", metrics, rows)

    ratio, score = _sample_scores(ref, cur, features)
    share = float((score == 1.0).mean())
    metrics.update({"datasetDrift": round(share, 4), "samplesInDistribution": int((score == 1.0).sum()),
                    "samplesLowDensity": int((score == 0.5).sum()), "samplesOutOfDistribution": int((score == 0.0).sum())})
    worst = np.argsort(ratio)[:50]
    shown = [c for c in features if not _is_text(cur[c])][:4] + [c for c in features if _is_text(cur[c])][:1]
    rows += [{"kind": "sample", "row": int(i) + 1, "score": float(score[i]), "densityRatio": round(float(ratio[i]), 4),
              **{c: _cell(cur[c].iloc[i]) for c in shown}} for i in worst if score[i] < 1.0]

    failed_features = [r["feature"] for r in rows if r.get("drifted")]
    if tabular:
        ok = not failed_features
        summary = (f"No feature drifted: largest PSI {metrics['maxPsi']} (limit {psi_limit})." if ok
                   else f"{len(failed_features)} of {len(tabular)} features drifted (PSI at or above {psi_limit}): {', '.join(failed_features[:6])}.")
    else:
        ok = share >= min_share
        summary = f"Only text features; judged on the share of current samples in distribution (limit {min_share})."
    summary += f" {share:.0%} of current samples are in distribution."
    return result("passed" if ok else "failed", summary, metrics, rows)


# --- helpers for the file-reading engines below ----------------------------------

def _frame(raw: bytes, what: str) -> pd.DataFrame:
    """The CSV with every cell kept as text, so leading zeros and ids survive."""
    read_csv(raw, what)
    return pd.read_csv(io.BytesIO(raw), dtype=str)


def _blank(series: pd.Series) -> pd.Series:
    return series.isna() | (series.str.strip() == "")


def _need(params: Dict[str, Any], name: str) -> str:
    value = str(params.get(name) or "").strip()
    if not value:
        raise EngineError(f"{name} is required")
    return value


def _json_param(params: Dict[str, Any], name: str) -> Dict[str, Any]:
    value = params.get(name)
    if value in (None, ""):
        raise EngineError(f"{name} is required")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError as exc:
            raise EngineError(f"{name} is not valid JSON: {exc}")
    if not isinstance(value, dict) or not value:
        raise EngineError(f"{name} must be a non-empty JSON object")
    return value


def _norm(frame: pd.DataFrame, cols: List[str]) -> pd.Series:
    """One comparable key per row: whitespace collapsed, lower case."""
    key = None
    for c in cols:
        v = frame[c].fillna("").str.replace(r"\s+", " ", regex=True).str.strip().str.lower()
        key = v if key is None else key + "\x1f" + v
    return key


# --- EV-DAT-02 data poisoning ------------------------------------------------------

RARE_TOKEN_SHARE = 0.05  # a trigger token is rare: in at most this share of the labelled rows
_TOKEN = re.compile(r"\w+")
_RUN = re.compile(r"(\S)\1{9,}")


def data_poisoning(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    df = _frame(files["dataset"], "The dataset")
    text_cols = split(params.get("text_columns"))
    if not text_cols:
        raise EngineError("text_columns is required: name the columns that hold text, comma-separated")
    label = str(params.get("label_column") or "").strip()
    columns(df, text_cols + ([label] if label else []), "The dataset")
    min_support = max(2, int(number(params, "min_support", 5)))
    limit = number(params, "max_flagged_share", 0.001)

    text = df[text_cols[0]].fillna("")
    for c in text_cols[1:]:
        text = text + " " + df[c].fillna("")
    findings: List[Tuple[int, str, str]] = []
    instruction_rows = set()
    for i, t in enumerate(text):
        for cat in dict.fromkeys(c for c, _ in scan(t, INSTRUCTIONS)):
            findings.append((i, cat, mask(next(m for c, m in scan(t, INSTRUCTIONS) if c == cat))))
            instruction_rows.add(i)
        run = _RUN.search(t)
        if run:
            findings.append((i, "repeated_characters", mask(run.group(0))))

    triggers: Dict[str, str] = {}
    if label:
        lab = df[label]
        share = lab.value_counts(normalize=True)
        tokens = [set(_TOKEN.findall(t.lower())) for t in text]
        seen, by_label = Counter(), defaultdict(Counter)
        for toks, l in zip(tokens, lab):
            if pd.isna(l):
                continue
            for tok in toks:
                seen[tok] += 1
                by_label[tok][l] += 1
        for tok, n in seen.items():
            if n < min_support or n > RARE_TOKEN_SHARE * lab.notna().sum():
                continue
            l, k = by_label[tok].most_common(1)[0]
            if k / n >= 0.95 and share[l] < 0.5:
                triggers[tok] = l
        for i, toks in enumerate(tokens):
            for tok in sorted(toks & triggers.keys()):
                findings.append((i, f"trigger_token (rows with it are labelled {triggers[tok]})", mask(tok)))

    flagged = {i for i, _, _ in findings}
    share_flagged = len(flagged) / len(df)
    metrics = {"rows": len(df), "flaggedRows": len(flagged), "flaggedShare": round(share_flagged, 6),
               "instructionRows": len(instruction_rows), "triggerTokens": len(triggers),
               "triggerTokenSamples": [mask(t) for t in sorted(triggers)[:20]]}
    ok = share_flagged <= limit + 1e-12
    summary = (f"{len(flagged)} of {len(df)} rows ({share_flagged:.2%}) were flagged, "
               f"{'within' if ok else 'above'} the limit of {limit:.2%}. Every flagged row must be reviewed by a person.")
    detail = [{"row": i + 1, "reason": reason, "snippet": snippet} for i, reason, snippet in findings]
    return result("passed" if ok else "failed", summary, metrics, detail)


# --- EV-DAT-03 representativeness --------------------------------------------------

def _coverage(data: pd.DataFrame, prod: pd.DataFrame) -> Tuple[float, float]:
    """Share of production rows with a dataset neighbour as close as the dataset's own 95th percentile."""
    d_parts, p_parts = [], []
    for c in (c for c in data.columns if c in prod.columns):
        dn, pn = pd.to_numeric(data[c], errors="coerce"), pd.to_numeric(prod[c], errors="coerce")
        if dn.notna().sum() == data[c].notna().sum() > 0 and pn.notna().sum() == prod[c].notna().sum():
            mean, sd, med = dn.mean(), dn.std(), dn.median()
            sd = sd if sd > 0 else 1.0
            d_parts.append(((dn.fillna(med) - mean) / sd).to_numpy()[:, None])
            p_parts.append(((pn.fillna(med) - mean) / sd).to_numpy()[:, None])
        else:
            cats = data[c].dropna().unique().astype(object)
            if 0 < len(cats) <= 50:
                for parts, frame in ((d_parts, data), (p_parts, prod)):
                    parts.append((frame[c].fillna("").to_numpy(dtype=object)[:, None] == cats[None, :]).astype(float))
    if not d_parts:
        raise EngineError("The production file and the dataset share no usable columns to measure coverage")
    if len(data) < 2:
        raise EngineError("The dataset needs at least two rows to measure coverage")
    D, P = np.hstack(d_parts), np.hstack(p_parts)
    nn = NearestNeighbors(n_neighbors=2).fit(D)
    threshold = float(np.quantile(nn.kneighbors(D)[0][:, 1], 0.95))
    nearest = nn.kneighbors(P, n_neighbors=1)[0][:, 0]
    return float((nearest <= threshold + 1e-12).mean()), threshold


def representativeness(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    df = _frame(files["dataset"], "The dataset")
    targets = _json_param(params, "targets")
    tol = number(params, "tolerance", 0.2)
    columns(df, list(targets), "The dataset")

    rows = []
    for attr, spec in targets.items():
        if not isinstance(spec, dict) or not spec:
            raise EngineError(f"targets for {attr} must be an object of group: share, such as {{\"female\": 0.5}}")
        values = df[attr].dropna().str.strip()
        if values.empty:
            raise EngineError(f"The dataset has no values in {attr}")
        observed = values.value_counts(normalize=True)
        for group, target in spec.items():
            try:
                t = float(target)
            except (TypeError, ValueError):
                raise EngineError(f"The target for {attr}={group} must be a number")
            if t < 0:
                raise EngineError(f"The target for {attr}={group} cannot be negative")
            o = float(observed.get(str(group).strip(), 0.0))
            gap = (o - t) / t if t > 0 else (0.0 if o == 0 else None)
            rows.append({"kind": "group", "attribute": attr, "group": str(group), "observed": round(o, 4), "target": t,
                         "relativeGap": None if gap is None else round(gap, 4),
                         "withinTolerance": gap is not None and abs(gap) <= tol + 1e-9})

    outside = [r for r in rows if not r["withinTolerance"]]
    gaps = [abs(r["relativeGap"]) for r in rows if r["relativeGap"] is not None]
    metrics: Dict[str, Any] = {"rows": len(df), "groups": len(rows), "groupsOutside": len(outside),
                               "largestGap": round(max(gaps), 4) if gaps else None}
    if files.get("production"):
        coverage, threshold = _coverage(df, _frame(files["production"], "The production file"))
        metrics.update({"coverage": round(coverage, 4), "coverageDistance": round(threshold, 4)})

    pct = f"{tol:.0%}"
    if outside:
        sample = "; ".join(f"{r['attribute']}={r['group']} observed {r['observed']:.2f} vs target {r['target']:.2f}" for r in outside[:3])
        summary = f"{len(outside)} of {len(rows)} groups are outside +/-{pct} of their target: {sample}."
    else:
        summary = f"All {len(rows)} groups are within +/-{pct} of their target (largest gap {metrics['largestGap']:.1%})."
    if "coverage" in metrics:
        summary += f" {metrics['coverage']:.0%} of production rows have a close match in the dataset."
    return result("failed" if outside else "passed", summary, metrics, rows)


# --- EV-DAT-04 completeness and accuracy ------------------------------------------------

_RULE_KEYS = {"required", "type", "min", "max", "allowed", "pattern"}
_TYPES = {"number", "integer", "string", "date", "email"}
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_FAILING_ROWS = 50
MAX_PERIODS = 1_000_000


def _check_rules(rules: Dict[str, Any]) -> None:
    for col, rule in rules.items():
        if not isinstance(rule, dict):
            raise EngineError(f"The rule for {col} must be an object such as {{\"required\": true, \"type\": \"integer\"}}")
        unknown = set(rule) - _RULE_KEYS
        if unknown:
            raise EngineError(f"The rule for {col} has unknown keys {', '.join(sorted(unknown))}; use {', '.join(sorted(_RULE_KEYS))}")
        if rule.get("type") is not None and rule["type"] not in _TYPES:
            raise EngineError(f"The type for {col} must be one of {', '.join(sorted(_TYPES))}")
        if ("min" in rule or "max" in rule) and rule.get("type") not in (None, "number", "integer"):
            raise EngineError(f"min and max on {col} only apply to number or integer columns")
        for key in ("min", "max"):
            if key in rule and not isinstance(rule[key], (int, float)):
                raise EngineError(f"{key} for {col} must be a number")
        if "allowed" in rule and not isinstance(rule["allowed"], list):
            raise EngineError(f"allowed for {col} must be a list")
        if "pattern" in rule:
            try:
                re.compile(rule["pattern"])
            except (re.error, TypeError) as exc:
                raise EngineError(f"pattern for {col} is not a valid regular expression: {exc}")


def _violations(values: pd.Series, rule: Dict[str, Any]) -> Dict[str, pd.Series]:
    """For each rule, a boolean series that is True where a present value breaks it."""
    def broken(ok) -> pd.Series:
        return pd.Series([not ok(v) for v in values], index=values.index, dtype=bool)

    out: Dict[str, pd.Series] = {}
    kind = rule.get("type") or ("number" if "min" in rule or "max" in rule else None)
    if kind in ("number", "integer"):
        nums = pd.to_numeric(values, errors="coerce")
        out[f"type:{kind}"] = nums.isna() | ((nums % 1 != 0) if kind == "integer" else False)
        if "min" in rule:
            out[f"min:{rule['min']}"] = nums < rule["min"]
        if "max" in rule:
            out[f"max:{rule['max']}"] = nums > rule["max"]
    elif kind == "date":
        out["type:date"] = pd.to_datetime(values, errors="coerce", format="mixed").isna()
    elif kind == "email":
        out["type:email"] = broken(lambda v: bool(_EMAIL.match(v)))
    if "allowed" in rule:
        allowed = {str(a).strip() for a in rule["allowed"]}
        out["allowed"] = broken(lambda v: v in allowed)
    if "pattern" in rule:
        rx = re.compile(rule["pattern"])
        out["pattern"] = broken(lambda v: bool(rx.search(v)))
    return out


def completeness(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    df = _frame(files["dataset"], "The dataset")
    rules = _json_param(params, "rules")
    _check_rules(rules)
    columns(df, list(rules), "The dataset")
    max_missing, min_pass = number(params, "max_missing", 0.05), number(params, "min_pass", 0.99)
    time_col = str(params.get("time_column") or "").strip()
    freq = str(params.get("expected_frequency") or "").strip()
    if bool(time_col) != bool(freq):
        raise EngineError("time_column and expected_frequency go together: set both or neither")
    if time_col:
        columns(df, [time_col], "The dataset")

    per_column, failing, over_missing, under_pass = [], [], [], []
    checked = broken = 0
    per_cap = max(1, MAX_FAILING_ROWS // len(rules))
    for col, rule in rules.items():
        blank = _blank(df[col])
        present = df[col][~blank].str.strip()
        flags = _violations(present, rule)
        bad = pd.Series(False, index=present.index)
        for f in flags.values():
            bad |= f
        pass_rate = round(1 - float(bad.mean()), 4) if flags and len(present) else None
        miss = float(blank.mean())
        per_column.append({"kind": "column", "column": col, "required": bool(rule.get("required")), "missingRate": round(miss, 4), "rulePassRate": pass_rate})
        if rule.get("required") and miss > max_missing + 1e-12:
            over_missing.append(col)
        if pass_rate is not None and pass_rate < min_pass - 1e-12:
            under_pass.append(col)
        if flags:
            checked, broken = checked + len(present), broken + int(bad.sum())
        taken = 0
        for name, flag in flags.items():
            for idx in flag[flag].index[: per_cap - taken]:
                failing.append({"kind": "failure", "row": int(idx) + 1, "column": col, "rule": name})
                taken += 1

    metrics: Dict[str, Any] = {"rows": len(df), "requiredFieldsOverMissingLimit": len(over_missing), "columnsBelowPassRate": len(under_pass),
                               "rulePassRate": round(1 - broken / checked, 4) if checked else None}
    periods: List[Dict[str, Any]] = []
    if time_col:
        stamps = pd.to_datetime(df[time_col], errors="coerce", format="mixed").dropna()
        if stamps.empty:
            raise EngineError(f"{time_col} has no readable dates")
        try:
            seen = stamps.dt.to_period(freq)
            expected = pd.period_range(seen.min(), seen.max(), freq=freq)
        except (ValueError, TypeError) as exc:
            raise EngineError(f"expected_frequency {freq!r} is not a usable period alias such as D, W, M or h: {exc}")
        if len(expected) > MAX_PERIODS:
            raise EngineError(f"{time_col} spans {len(expected):,} periods at {freq}; use a coarser expected_frequency")
        gone = expected[~expected.isin(seen.unique())]
        metrics.update({"expectedPeriods": len(expected), "missingPeriods": len(gone)})
        periods = [{"kind": "period", "period": str(p)} for p in gone[:20]]

    ok = not over_missing and not under_pass
    if ok:
        summary = (f"Every required field is at most {max_missing:.0%} missing and every rule passes at least {min_pass:.0%}"
                   + (f" (overall {metrics['rulePassRate']:.1%})." if checked else "."))
    else:
        parts = []
        if over_missing:
            parts.append(f"{len(over_missing)} required field(s) are more than {max_missing:.0%} missing ({', '.join(over_missing[:5])})")
        if under_pass:
            parts.append(f"{len(under_pass)} column(s) pass less than {min_pass:.0%} of their rules ({', '.join(under_pass[:5])})")
        summary = "; ".join(parts).capitalize() + "."
    if time_col:
        summary += f" {metrics['missingPeriods']} of {metrics['expectedPeriods']} expected {freq} periods have no rows."
    return result("passed" if ok else "failed", summary, metrics, per_column + failing[:MAX_FAILING_ROWS] + periods)


# --- EV-DAT-05 duplicates and leakage -------------------------------------------------------

def duplicates(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    train = _frame(files["train"], "The train set")
    id_col = str(params.get("id_column") or "").strip()
    skip = set(split(params.get("ignore")))
    limit = number(params, "max_duplicate_rate", 0.01)
    if id_col:
        columns(train, [id_col], "The train set")
    content = [c for c in train.columns if c != id_col and c not in skip]
    if not content:
        raise EngineError("No columns are left to compare once the id column and ignored columns are removed")

    key = _norm(train, content)
    repeat = key.duplicated()
    rate = float(repeat.mean())
    metrics: Dict[str, Any] = {"trainRows": len(train), "duplicateRows": int(repeat.sum()), "duplicateRate": round(rate, 6)}
    if id_col:
        ids = train[id_col]
        present = ids[~_blank(ids)]
        metrics.update({"idPresentRate": round(len(present) / len(train), 4), "duplicateIds": int(present.duplicated().sum())})

    groups = key[key.duplicated(keep=False)].groupby(key).apply(lambda s: [int(i) + 1 for i in s.index])
    detail: List[Dict[str, Any]] = [{"kind": "duplicate_group", "count": len(r), "rows": r[:20]}
                                    for r in sorted(groups, key=len, reverse=True)]
    leaked = 0
    test_file = files.get("test")
    if test_file:
        test = _frame(test_file, "The test set")
        columns(test, content, "The test set")
        first = dict(zip(key[::-1], train.index[::-1] + 1))
        hit = _norm(test, content).map(first)
        leaked = int(hit.notna().sum())
        metrics.update({"testRows": len(test), "overlappingTestRows": leaked})
        detail += [{"kind": "overlap", "testRow": int(i) + 1, "trainRow": int(hit[i])} for i in hit[hit.notna()].index]

    ok = rate <= limit + 1e-12 and leaked == 0
    summary = f"{metrics['duplicateRows']} of {len(train)} train rows ({rate:.2%}) repeat an earlier row (limit {limit:.2%})."
    if test_file:
        summary += f" {leaked} of {metrics['testRows']} test rows also appear in the train set."
    return result("passed" if ok else "failed", summary, metrics, detail)


# --- EV-DAT-06 personal data ---------------------------------------------------------------------

def personal_data(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    df = _frame(files["dataset"], "The dataset")
    cols = split(params.get("columns")) or list(df.columns)
    columns(df, cols, "The dataset")
    detectors = PERSONAL + SECRETS
    approved = set(split(params.get("approved")))
    unknown = approved - {d[0] for d in detectors}
    if unknown:
        raise EngineError(f"approved names unknown categories {', '.join(sorted(unknown))}; known: {', '.join(d[0] for d in detectors)}")

    by_category: Counter = Counter()
    hit_rows = set()
    detail: List[Dict[str, Any]] = []
    for col in cols:
        for i, value in df[col].dropna().items():
            for cat, matched in scan(value, detectors):
                by_category[cat] += 1
                hit_rows.add(i)
                detail.append({"row": int(i) + 1, "column": col, "category": cat, "maskedValue": mask(matched), "approved": cat in approved})
    detail.sort(key=lambda r: (r["approved"], r["row"]))

    unapproved = sum(n for c, n in by_category.items() if c not in approved)
    metrics = {"rows": len(df), "columnsScanned": len(cols), "rowsWithHits": len(hit_rows), "totalHits": sum(by_category.values()),
               "unapprovedHits": unapproved, "hitsPer1000": {c: round(n / len(df) * 1000, 2) for c, n in sorted(by_category.items())}}
    bad = sorted(c for c in by_category if c not in approved)
    summary = (f"No personal data or secrets found in {len(cols)} columns." if not by_category else
               f"{metrics['totalHits']} hits in {len(hit_rows)} of {len(df)} rows; " +
               (f"unapproved categories: {', '.join(bad)}." if bad else "every category found is approved."))
    return result("failed" if unapproved else "passed", summary, metrics, detail)


# --- EV-DAT-07 retrieval poisoning -------------------------------------------------------------------

def rag_poisoning(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    df = _frame(files["documents"], "The documents file")
    text_col = _need(params, "text_column")
    id_col = str(params.get("id_column") or "").strip()
    columns(df, [text_col] + ([id_col] if id_col else []), "The documents file")

    detail: List[Dict[str, Any]] = []
    by_category: Counter = Counter()
    for i, text in df[text_col].dropna().items():
        hits = scan(text, INSTRUCTIONS)
        if not hits:
            continue
        cats = sorted({c for c, _ in hits})
        by_category.update(cats)
        doc = df[id_col].iloc[i] if id_col and not pd.isna(df[id_col].iloc[i]) else f"row {int(i) + 1}"
        detail.append({"document": str(doc), "categories": cats, "snippet": mask(hits[0][1])})

    metrics = {"documents": len(df), "flaggedDocuments": len(detail), "byCategory": dict(sorted(by_category.items()))}
    summary = (f"No document among {len(df)} contains hidden instructions." if not detail else
               f"{len(detail)} of {len(df)} documents contain hidden instructions ({', '.join(sorted(by_category))}) and must be reviewed.")
    return result("failed" if detail else "passed", summary, metrics, detail)


# --- EV-DAT-08 label quality ------------------------------------------------------------------------------

MIN_LABELLED = 30


def label_quality(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    df = _frame(files["labels"], "The labels file")
    a, b = _need(params, "first_annotator"), _need(params, "second_annotator")
    gold = str(params.get("gold") or "").strip()
    columns(df, [a, b] + ([gold] if gold else []), "The labels file")
    min_kappa, max_error = number(params, "min_kappa", 0.8), number(params, "max_error", 0.02)

    both = df[[a, b]].dropna().apply(lambda c: c.str.strip())
    metrics: Dict[str, Any] = {"rows": len(df), "doublyLabelledRows": len(both)}
    if len(both) < MIN_LABELLED:
        return result("insufficient", f"Label agreement needs at least {MIN_LABELLED} rows labelled by both annotators; got {len(both)}.", metrics)

    agreement = float((both[a] == both[b]).mean())
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        kappa = float(cohen_kappa_score(both[a], both[b]))
    if np.isnan(kappa):  # both annotators used one label throughout
        kappa = 1.0 if agreement == 1 else 0.0
    metrics.update({"kappa": round(kappa, 4), "agreement": round(agreement, 4)})

    pairs = both.value_counts().reset_index()
    detail = sorted(({"kind": "pair", "first": r[a], "second": r[b], "count": int(r["count"]), "agree": r[a] == r[b]}
                     for _, r in pairs.iterrows()), key=lambda r: (r["agree"], -r["count"]))
    ok = kappa >= min_kappa - 1e-12
    summary = f"Cohen's kappa is {kappa:.2f} (limit {min_kappa:.2f}) with {agreement:.1%} raw agreement on {len(both)} rows."
    if gold:
        audited = df[[a, gold]].dropna().apply(lambda c: c.str.strip())
        if audited.empty:
            raise EngineError(f"{gold} has no audited labels")
        wrong = audited[audited[a] != audited[gold]]
        error = len(wrong) / len(audited)
        metrics.update({"auditedRows": len(audited), "errorRate": round(error, 4)})
        detail += [{"kind": "gold_pair", "first": k[0], "gold": k[1], "count": int(n)} for k, n in wrong.value_counts().items()]
        ok = ok and error <= max_error + 1e-12
        summary += f" {a} disagrees with the audited label on {error:.1%} of {len(audited)} rows (limit {max_error:.1%})."
    return result("passed" if ok else "failed", summary, metrics, detail)


ENGINES: List[Engine] = [
    Engine(
        id="EV-DAT-01",
        method=(
            "PSI and the Kolmogorov-Smirnov statistic per tabular feature against the reference, and a per-sample "
            "density ratio from a classifier trained to tell the reference from the current set (out-of-fold). "
            "A sample scores 1.0 when its ratio is at least 0.5, 0.5 down to 0.1, and 0.0 below."
        ),
        slots=(
            Slot("reference", "Reference set", "The data the model was trained or validated on, as CSV."),
            Slot("current", "Current set", "Production or new data with the same columns, as CSV."),
        ),
        params=(
            Param("features", "Features", "Columns to compare, comma-separated. Blank compares every shared column."),
            Param("ignore", "Ignore", "Columns to leave out, such as identifiers or timestamps."),
            Param("psi_limit", "PSI limit", "A feature drifts at or above this PSI.", "number", 0.2),
            Param("min_in_distribution", "Minimum share in distribution", "Used when every feature is text.", "number", 0.9),
        ),
        run=data_drift,
    ),
    Engine(
        id="EV-DAT-02",
        method=(
            "Flags rows that match instruction-injection patterns, contain a long run of one repeated character, or "
            "(when a label column is set) contain a rare token that sits in at least the minimum number of rows, 95% of them "
            "with one label that is under half the data."
        ),
        slots=(Slot("dataset", "Dataset", "The training or fine-tuning data as CSV."),),
        params=(
            Param("text_columns", "Text columns", "Columns that hold text, comma-separated.", required=True),
            Param("label_column", "Label column", "Optional. Enables the trigger-token check."),
            Param("min_support", "Minimum support", "A trigger token must appear in at least this many rows.", "number", 5),
            Param("max_flagged_share", "Flagged share limit", "The run passes at or below this share of rows flagged.", "number", 0.001),
        ),
        run=data_poisoning,
    ),
    Engine(
        id="EV-DAT-03",
        method=(
            "Compares each group's observed share with its target as a relative gap, and optionally reports the share of "
            "production rows whose nearest dataset neighbour is within the 95th percentile of dataset-to-dataset distances."
        ),
        slots=(
            Slot("dataset", "Dataset", "The data to check, as CSV."),
            Slot("production", "Production data", "Optional. Live or expected data with the same columns, for the coverage figure.", required=False),
        ),
        params=(
            Param("targets", "Targets", "JSON of target shares per attribute, such as {\"gender\": {\"female\": 0.5, \"male\": 0.5}}.", "json", required=True),
            Param("tolerance", "Tolerance", "Allowed relative gap from the target.", "number", 0.2),
        ),
        run=representativeness,
    ),
    Engine(
        id="EV-DAT-04",
        method=(
            "Measures the missing rate of each required field and the share of present values that pass each column's rules "
            "(type, range, allowed values, pattern), plus missing periods when a time column and frequency are given."
        ),
        slots=(Slot("dataset", "Dataset", "The data to check, as CSV."),),
        params=(
            Param("rules", "Rules", "JSON per column, such as {\"age\": {\"required\": true, \"type\": \"integer\", \"min\": 0, \"max\": 120}}. "
                  "Keys: required, type (number, integer, string, date, email), min, max, allowed, pattern.", "json", required=True),
            Param("max_missing", "Missing limit", "Largest allowed missing share in a required field.", "number", 0.05),
            Param("min_pass", "Rule pass rate", "Smallest allowed share of present values passing a column's rules.", "number", 0.99),
            Param("time_column", "Time column", "Optional. A date column to check for gaps."),
            Param("expected_frequency", "Expected frequency", "Pandas period alias for the time column, such as D, W, M or h."),
        ),
        run=completeness,
    ),
    Engine(
        id="EV-DAT-05",
        method=(
            "Normalises whitespace and case across the non-id columns, counts rows that repeat an earlier row, and counts "
            "test rows whose normalised content also appears in the train set."
        ),
        slots=(
            Slot("train", "Train set", "The training data as CSV."),
            Slot("test", "Test set", "Optional. Held-out data with the same columns, checked for leakage into train.", required=False),
        ),
        params=(
            Param("id_column", "Id column", "Optional. Reported for presence and uniqueness, and left out of the comparison."),
            Param("ignore", "Ignore", "Columns to leave out of the comparison, such as labels or timestamps."),
            Param("max_duplicate_rate", "Duplicate limit", "Largest allowed share of repeated rows.", "number", 0.01),
        ),
        run=duplicates,
    ),
    Engine(
        id="EV-DAT-06",
        method=(
            "Scans every cell for personal identifiers (checksum-validated where one exists) and secrets, and fails on any "
            "hit in a category that has not been approved."
        ),
        slots=(Slot("dataset", "Dataset", "The training or retrieval data as CSV."),),
        params=(
            Param("approved", "Approved categories", "Categories allowed to appear, comma-separated, such as email,phone. Blank approves none."),
            Param("columns", "Columns", "Columns to scan. Blank scans every column."),
        ),
        run=personal_data,
    ),
    Engine(
        id="EV-DAT-07",
        method="Scans each document for instructions planted in the text, such as overrides, fake turns, hidden markup and exfiltration links.",
        slots=(Slot("documents", "Documents", "One document per row, as CSV."),),
        params=(
            Param("text_column", "Text column", "The column that holds the document text.", required=True),
            Param("id_column", "Id column", "Optional. Names flagged documents; otherwise the row number is used."),
        ),
        run=rag_poisoning,
    ),
    Engine(
        id="EV-DAT-08",
        method=(
            "Cohen's kappa and raw agreement between two annotators, and the error rate of the first annotator "
            "against an audited gold column when one is given."
        ),
        slots=(Slot("labels", "Labels", "A CSV with one column per annotator and optionally an audited gold column."),),
        params=(
            Param("first_annotator", "First annotator", "Column with the first annotator's labels.", required=True),
            Param("second_annotator", "Second annotator", "Column with the second annotator's labels.", required=True),
            Param("gold", "Gold column", "Optional. The audited correct label."),
            Param("min_kappa", "Minimum kappa", "Smallest allowed Cohen's kappa.", "number", 0.8),
            Param("max_error", "Error limit", "Largest allowed audited error rate of the first annotator.", "number", 0.02),
        ),
        run=label_quality,
    ),
]
