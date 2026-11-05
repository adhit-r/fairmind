"""Engines that read model outputs: accuracy, calibration, slices, counterfactuals, monitoring, privacy attacks, verbatim reproduction."""

import math
import re
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support, roc_auc_score, roc_curve

from .common import Engine, EngineError, Param, Slot, columns, number, read_csv, read_text, result, split


def _name(params: Dict[str, Any], key: str, default: str) -> str:
    value = params.get(key)
    return default if value in (None, "") else str(value).strip()


def _optional(params: Dict[str, Any], key: str) -> Optional[float]:
    return None if params.get(key) in (None, "") else number(params, key, 0.0)


def _rows(files: Dict[str, bytes], slot: str, what: str, cols: List[str]) -> pd.DataFrame:
    """The slot's CSV, reduced to the named columns with incomplete rows dropped."""
    frame = read_csv(files[slot], what)
    columns(frame, cols, what)
    rows = frame[cols].dropna()
    if rows.empty:
        raise EngineError(f"{what} has no row with a value in every one of {', '.join(cols)}")
    return rows.reset_index(drop=True)


def _labels(series: pd.Series) -> pd.Series:
    """Labels as comparable text, so 1, 1.0 and "1" are the same label."""
    if pd.api.types.is_numeric_dtype(series) and (series.astype(float) % 1 == 0).all():
        return series.astype(float).astype(int).astype(str)
    return series.astype(str).str.strip()


def _label(value: Any) -> str:
    return str(_labels(pd.Series([value])).iloc[0])


def _binary(series: pd.Series, name: str) -> np.ndarray:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.isna().any() or not numeric.isin([0, 1]).all():
        raise EngineError(f"{name} must be 0 or 1 in every row")
    return numeric.to_numpy(int)


def _numeric(series: pd.Series, name: str) -> np.ndarray:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.isna().any():
        raise EngineError(f"{name} must be a number in every row")
    return numeric.to_numpy(float)


def _r(value: Optional[float], digits: int = 4) -> Optional[float]:
    return None if value is None else round(float(value), digits)


def _verdict(ok: bool) -> str:
    return "passed" if ok else "failed"


# EV-TST-01 -------------------------------------------------------------------------------------------------

def task_accuracy(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    yt, yp = _name(params, "y_true", "y_true"), _name(params, "y_pred", "y_pred")
    task = _name(params, "task", "classification").lower()
    if task not in ("classification", "regression"):
        raise EngineError("task must be classification or regression")
    d = _rows(files, "predictions", "The predictions", [yt, yp])
    baseline, last = _optional(params, "baseline"), _optional(params, "last_release")
    max_drop = number(params, "max_drop", 0.02)

    detail: List[Dict[str, Any]] = []
    if task == "classification":
        t, p = _labels(d[yt]), _labels(d[yp])
        labels = sorted(set(t) | set(p))
        prec, rec, _, support = precision_recall_fscore_support(t, p, labels=labels, zero_division=0)
        detail = [{"class": c, "precision": _r(a), "recall": _r(b), "support": int(s)} for c, a, b, s in zip(labels, prec, rec, support)]
        value = float(accuracy_score(t, p))
        metrics: Dict[str, Any] = {"rows": len(d), "metric": "accuracy", "value": _r(value), "accuracy": _r(value),
                                   "macroF1": _r(f1_score(t, p, labels=labels, average="macro", zero_division=0))}
        better = lambda cur, ref: cur >= ref  # noqa: E731
        change = lambda cur, ref: ref - cur  # noqa: E731  points lost
        unit = "accuracy"
    else:
        err = _numeric(d[yt], yt) - _numeric(d[yp], yp)
        t = _numeric(d[yt], yt)
        value = float(np.abs(err).mean())
        ss_tot = float(((t - t.mean()) ** 2).sum())
        metrics = {"rows": len(d), "metric": "mae", "value": _r(value), "mae": _r(value), "rmse": _r(math.sqrt(float((err ** 2).mean()))),
                   "r2": _r(1 - float((err ** 2).sum()) / ss_tot) if ss_tot > 0 else None}
        better = lambda cur, ref: cur <= ref  # noqa: E731
        change = lambda cur, ref: (cur - ref) / ref if ref else float("inf") if cur > ref else 0.0  # noqa: E731  relative MAE increase
        unit = "MAE"

    metrics.update({"baseline": baseline, "lastRelease": last})
    if baseline is None:
        return result("insufficient", f"No agreed baseline was given, so there is nothing to judge {unit} {value:.4f} against.", metrics, detail)
    ok = better(value, baseline)
    summary = f"{unit} is {value:.4f} against an agreed baseline of {baseline:g}"
    if last is not None:
        drop = change(value, last)
        metrics["dropVsLastRelease"] = _r(drop)
        ok = ok and drop <= max_drop
        summary += f" and {last:g} in the last release ({'drop' if task == 'classification' else 'relative increase'} {drop:.4f}, limit {max_drop:g})"
    return result(_verdict(ok), summary + ".", metrics, detail)


# EV-TST-02 -------------------------------------------------------------------------------------------------

def _normalise(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text).lower()).strip().rstrip(" .,!?;:")


def answer_consistency(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    pc, ac = _name(params, "prompt_column", "prompt"), _name(params, "answer_column", "answer")
    threshold = number(params, "similarity", 0.8)
    min_share = number(params, "min_consistent", 0.9)
    d = _rows(files, "answers", "The answers", [pc, ac])
    d["norm"] = d[ac].map(_normalise)
    try:
        vectors = TfidfVectorizer().fit_transform(d["norm"])
    except ValueError:  # every answer is empty or only stop-characters
        vectors = None
    norm = d["norm"].to_numpy()

    total, bad = 0, []
    for prompt, idx in d.groupby(pc, sort=False).indices.items():
        if len(idx) < 2:
            continue
        total += 1
        same = norm[idx][:, None] == norm[idx][None, :]
        sim = (vectors[idx] @ vectors[idx].T).toarray() if vectors is not None else np.zeros((len(idx), len(idx)))
        lowest = float(np.where(same, 1.0, sim)[np.triu_indices(len(idx), 1)].min())
        if lowest < threshold - 1e-9:
            bad.append({"prompt": str(prompt)[:200], "answers": len(idx), "lowestSimilarity": round(lowest, 4)})
    metrics: Dict[str, Any] = {"prompts": int(d[pc].nunique()), "promptsWithRepeats": total, "inconsistentPrompts": len(bad)}
    if total == 0:
        return result("insufficient", "No prompt has two or more answers, so consistency cannot be measured.", metrics)
    share = 1 - len(bad) / total
    metrics["consistentShare"] = round(share, 4)
    bad.sort(key=lambda r: r["lowestSimilarity"])
    return result(_verdict(share >= min_share), f"{share:.1%} of {total} prompts with repeated answers are consistent (limit {min_share:.0%}); {len(bad)} are not.", metrics, bad)


# EV-TST-07 -------------------------------------------------------------------------------------------------

def calibration(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    yt, sc = _name(params, "y_true", "y_true"), _name(params, "score", "score")
    bins = int(number(params, "bins", 10))
    max_ece = number(params, "max_ece", 0.05)
    if bins < 1:
        raise EngineError("bins must be at least 1")
    d = _rows(files, "predictions", "The predictions", [yt, sc])
    y, s = _binary(d[yt], yt), _numeric(d[sc], sc)
    if s.min() < 0 or s.max() > 1:
        raise EngineError(f"{sc} must be a probability between 0 and 1")
    which = np.minimum((s * bins).astype(int), bins - 1)
    ece, detail = 0.0, []
    for b in range(bins):
        m = which == b
        if not m.any():
            continue
        ece += m.mean() * abs(y[m].mean() - s[m].mean())
        detail.append({"bin": f"{b / bins:.2f}-{(b + 1) / bins:.2f}", "count": int(m.sum()), "meanScore": _r(s[m].mean()), "observedRate": _r(y[m].mean())})
    metrics = {"rows": len(d), "bins": bins, "ece": _r(ece)}
    return result(_verdict(ece <= max_ece), f"Expected calibration error is {ece:.4f} over {bins} equal-width bins (limit {max_ece:g}).", metrics, detail)


# EV-TST-08 -------------------------------------------------------------------------------------------------

def ood_detection(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    sc, flag = _name(params, "score", "score"), _name(params, "is_ood", "is_ood")
    min_auroc = _optional(params, "min_auroc")
    d = _rows(files, "scores", "The scores", [sc, flag])
    y, s = _binary(d[flag], flag), _numeric(d[sc], sc)
    metrics: Dict[str, Any] = {"rows": len(d), "inDistribution": int((y == 0).sum()), "outOfDistribution": int((y == 1).sum()), "minAuroc": min_auroc}
    if len(set(y)) < 2:
        return result("insufficient", f"{flag} needs both in-distribution (0) and out-of-distribution (1) rows to compute an AUROC.", metrics)
    auroc = float(roc_auc_score(y, s))
    fpr, tpr, _ = roc_curve(y, s)
    metrics.update({"auroc": _r(auroc), "fprAt95Tpr": _r(fpr[np.searchsorted(tpr, 0.95, side="left")])})
    if min_auroc is None:
        return result("insufficient", f"AUROC is {auroc:.4f}, but no agreed minimum AUROC was given to judge it against.", metrics)
    return result(_verdict(auroc >= min_auroc), f"AUROC is {auroc:.4f} against an agreed minimum of {min_auroc:g}; the false positive rate at 95% true positive rate is {metrics['fprAt95Tpr']:.4f}.", metrics)


# EV-TST-10 -------------------------------------------------------------------------------------------------

def multilingual_parity(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    yt, yp, lc = _name(params, "y_true", "y_true"), _name(params, "y_pred", "y_pred"), _name(params, "language", "language")
    max_gap, min_rows = number(params, "max_gap", 0.05), int(number(params, "min_rows", 30))
    d = _rows(files, "predictions", "The predictions", [yt, yp, lc])
    d["ok"] = (_labels(d[yt]) == _labels(d[yp])).to_numpy()
    detail = []
    for lang, g in d.groupby(lc, sort=True):
        detail.append({"language": str(lang), "records": len(g), "accuracy": _r(g["ok"].mean()), "skipped": len(g) < min_rows})
    kept = [r for r in detail if not r["skipped"]]
    metrics: Dict[str, Any] = {"rows": len(d), "languages": len(detail), "languagesCompared": len(kept)}
    if len(kept) < 2:
        return result("insufficient", f"Fewer than two languages have {min_rows} or more rows ({len(kept)}), so parity cannot be measured.", metrics, detail)
    best, worst = max(kept, key=lambda r: r["accuracy"]), min(kept, key=lambda r: r["accuracy"])
    gap = best["accuracy"] - worst["accuracy"]
    metrics.update({"gap": _r(gap), "best": best["language"], "worst": worst["language"]})
    detail.sort(key=lambda r: (r["skipped"], -r["accuracy"]))
    return result(_verdict(gap <= max_gap), f"Accuracy gap across {len(kept)} languages is {gap:.4f} (limit {max_gap:g}): {best['language']} {best['accuracy']:.4f} to {worst['language']} {worst['accuracy']:.4f}.", metrics, detail)


# EV-TST-11 -------------------------------------------------------------------------------------------------

def selective_accuracy(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    yt, yp, cf = _name(params, "y_true", "y_true"), _name(params, "y_pred", "y_pred"), _name(params, "confidence", "confidence")
    coverage, min_acc = number(params, "coverage", 0.8), _optional(params, "min_accuracy")
    if not 0 < coverage <= 1:
        raise EngineError("coverage must be above 0 and at most 1")
    d = _rows(files, "predictions", "The predictions", [yt, yp, cf])
    conf = _numeric(d[cf], cf)
    correct = (_labels(d[yt]) == _labels(d[yp])).to_numpy()[np.argsort(-conf, kind="stable")]
    n = len(d)
    kept = max(1, math.ceil(coverage * n - 1e-9))
    selective = float(correct[:kept].mean())
    curve = []
    for step in range(1, 11):
        k = max(1, math.ceil(step / 10 * n - 1e-9))
        curve.append({"coverage": step / 10, "records": k, "accuracy": _r(correct[:k].mean()), "risk": _r(1 - correct[:k].mean())})
    metrics = {"rows": n, "coverage": coverage, "answered": kept, "selectiveAccuracy": _r(selective), "overallAccuracy": _r(correct.mean()), "minAccuracy": min_acc}
    if min_acc is None:
        return result("insufficient", f"Accuracy on the most confident {coverage:.0%} is {selective:.4f}, but no agreed minimum accuracy was given.", metrics, curve)
    return result(_verdict(selective >= min_acc), f"Accuracy on the most confident {coverage:.0%} of {n} records is {selective:.4f} against an agreed minimum of {min_acc:g} (overall {correct.mean():.4f}).", metrics, curve)


# EV-FAI-03 -------------------------------------------------------------------------------------------------

def intersectional_slices(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    attrs = split(params.get("attributes"))
    if len(attrs) < 2:
        raise EngineError("attributes needs at least two column names, comma-separated")
    yp, yt = _name(params, "y_pred", "y_pred"), params.get("y_true") and _name(params, "y_true", "y_true")
    fav = _label(params.get("favorable", 1) if params.get("favorable") not in (None, "") else 1)
    max_gap, min_slice = number(params, "max_gap", 0.1), int(number(params, "min_slice", 30))
    d = _rows(files, "decisions", "The decisions", attrs + [yp] + ([yt] if yt else []))
    sel = (_labels(d[yp]) == fav).to_numpy()
    pos = (_labels(d[yt]) == fav).to_numpy() if yt else None

    detail = []
    for key, idx in d.groupby(attrs, sort=True).indices.items():
        key = key if isinstance(key, tuple) else (key,)
        row: Dict[str, Any] = {"slice": ", ".join(f"{a}={v}" for a, v in zip(attrs, key)), "records": len(idx), "skipped": len(idx) < min_slice,
                               "selectionRate": _r(sel[idx].mean()), "truePositiveRate": None}
        if pos is not None and pos[idx].any():
            row["truePositiveRate"] = _r(sel[idx][pos[idx]].mean())
        detail.append(row)
    kept = [r for r in detail if not r["skipped"]]
    metrics: Dict[str, Any] = {"rows": len(d), "slices": len(detail), "slicesCompared": len(kept)}
    if len(kept) < 2:
        return result("insufficient", f"Fewer than two intersections have {min_slice} or more records ({len(kept)}), so gaps cannot be measured.", metrics, detail)
    rates = [r["selectionRate"] for r in kept]
    gap = max(rates) - min(rates)
    tprs = [r["truePositiveRate"] for r in kept if r["truePositiveRate"] is not None]
    tpr_gap = max(tprs) - min(tprs) if len(tprs) >= 2 else None
    metrics.update({"selectionRateGap": _r(gap), "truePositiveRateGap": _r(tpr_gap)})
    hi, lo = max(kept, key=lambda r: r["selectionRate"]), min(kept, key=lambda r: r["selectionRate"])
    ok = gap <= max_gap and (tpr_gap is None or tpr_gap <= max_gap)
    summary = f"Selection rate gap across {len(kept)} intersections is {gap:.4f} (limit {max_gap:g}): {hi['slice']} {hi['selectionRate']:.4f} to {lo['slice']} {lo['selectionRate']:.4f}."
    if tpr_gap is not None:
        summary += f" True positive rate gap is {tpr_gap:.4f}."
    detail.sort(key=lambda r: (r["skipped"], -r["selectionRate"]))
    return result(_verdict(ok), summary, metrics, detail)


# EV-FAI-04 -------------------------------------------------------------------------------------------------

def counterfactual_fairness(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    oc, cc = _name(params, "original_column", "original"), _name(params, "counterfactual_column", "counterfactual")
    pc, pr = _name(params, "pair_column", "pair_id"), _name(params, "prediction_column", "prediction")
    max_flip = number(params, "max_flip_rate", 0.02)
    frame = read_csv(files["pairs"], "The pairs")
    flipped: List[Dict[str, Any]] = []
    if oc in frame.columns and cc in frame.columns:
        d = frame[[oc, cc]].dropna().reset_index(drop=True)
        a, b = _labels(d[oc]), _labels(d[cc])
        total = len(d)
        flipped = [{"pair": int(i) + 1, "original": a[i], "counterfactual": b[i]} for i in np.flatnonzero((a != b).to_numpy())]
    elif pc in frame.columns and pr in frame.columns:
        d = frame[[pc, pr]].dropna()
        d = d.assign(label=_labels(d[pr]))
        groups = [(k, g["label"].tolist()) for k, g in d.groupby(pc, sort=False) if len(g) >= 2]
        total = len(groups)
        flipped = [{"pair": str(k), "predictions": " / ".join(v)} for k, v in groups if len(set(v)) > 1]
    else:
        raise EngineError(f"The pairs file needs columns {oc} and {cc}, or {pc} and {pr}; it has {', '.join(map(str, frame.columns[:20]))}")
    metrics: Dict[str, Any] = {"pairs": total, "flipped": len(flipped)}
    if total == 0:
        return result("insufficient", "No complete pairs were found, so the flip rate cannot be measured.", metrics)
    rate = len(flipped) / total
    metrics["flipRate"] = round(rate, 4)
    return result(_verdict(rate <= max_flip), f"{len(flipped)} of {total} pairs changed prediction when the protected attribute changed: flip rate {rate:.2%} (limit {max_flip:.0%}).", metrics, flipped)


# EV-MON-01 -------------------------------------------------------------------------------------------------

def _score(d: pd.DataFrame, yt: str, yp: str, metric: str) -> float:
    t, p = _labels(d[yt]), _labels(d[yp])
    if metric == "accuracy":
        return float(accuracy_score(t, p))
    return float(f1_score(t, p, labels=sorted(set(t) | set(p)), average="macro", zero_division=0))


def production_degradation(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    yt, yp = _name(params, "y_true", "y_true"), _name(params, "y_pred", "y_pred")
    metric = _name(params, "metric", "accuracy").lower()
    if metric not in ("accuracy", "f1"):
        raise EngineError("metric must be accuracy or f1")
    max_drop, given = number(params, "max_relative_drop", 0.05), _optional(params, "baseline_value")
    current = _score(_rows(files, "production", "The production outcomes", [yt, yp]), yt, yp, metric)
    metrics: Dict[str, Any] = {"metric": metric, "current": _r(current)}
    if files.get("baseline"):
        baseline = _score(_rows(files, "baseline", "The baseline outcomes", [yt, yp]), yt, yp, metric)
    else:
        baseline = given
    if baseline is None:
        return result("insufficient", f"Production {metric} is {current:.4f}, but there is neither a baseline file nor a baseline value to compare it with.", metrics)
    if baseline <= 0:
        raise EngineError("The baseline must be above zero to measure a relative drop")
    drop = (baseline - current) / baseline
    metrics.update({"baseline": _r(baseline), "relativeDrop": _r(drop)})
    return result(_verdict(drop <= max_drop), f"Production {metric} is {current:.4f} against a baseline of {baseline:.4f}: relative drop {drop:.2%} (limit {max_drop:.0%}).", metrics)


# EV-PRV-02 -------------------------------------------------------------------------------------------------

def membership_inference(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    sc, member = _name(params, "score", "score"), _name(params, "is_member", "is_member")
    max_auc = number(params, "max_auc", 0.6)
    d = _rows(files, "attack", "The attack scores", [sc, member])
    y, s = _binary(d[member], member), _numeric(d[sc], sc)
    metrics: Dict[str, Any] = {"members": int((y == 1).sum()), "nonMembers": int((y == 0).sum())}
    if len(set(y)) < 2:
        return result("insufficient", f"{member} needs both member (1) and non-member (0) records to run the attack.", metrics)
    raw = float(roc_auc_score(y, s))
    auc = max(raw, 1 - raw)
    metrics.update({"attackAuc": _r(auc), "rawAuc": _r(raw)})
    return result(_verdict(auc <= max_auc), f"The membership attack reaches AUC {auc:.4f} (limit {max_auc:g}); 0.5 means it cannot tell members from non-members.", metrics)


# EV-LEG-01 -------------------------------------------------------------------------------------------------

def _words(text: Any) -> List[str]:
    return re.findall(r"\w+", str(text).lower())


def verbatim_reproduction(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    tc, limit = _name(params, "text_column", "output"), int(number(params, "limit_words", 50))
    if limit < 1:
        raise EngineError("limit_words must be at least 1")
    frame = read_csv(files["outputs"], "The outputs")
    columns(frame, [tc], "The outputs")
    works = [w for w in (_words(part) for part in re.split(r"^[ \t]*---[ \t]*$", read_text(files["protected"], "The protected text"), flags=re.M)) if w]
    if not works:
        raise EngineError("The protected text has no words")

    # Index every k-gram of every work; a shared run of limit or more words contains one, then extend it word by word.
    k = max(1, min(6, limit))
    index: Dict[tuple, List[tuple]] = {}
    for w, words in enumerate(works):
        for p in range(len(words) - k + 1):
            index.setdefault(tuple(words[p:p + k]), []).append((w, p))

    detail, longest = [], 0
    for row, text in enumerate(frame[tc].fillna("")):
        out = _words(text)
        best, at = 0, 0
        for i in range(len(out) - k + 1):
            for w, p in index.get(tuple(out[i:i + k]), ()):
                if i and p and out[i - 1] == works[w][p - 1]:
                    continue  # already inside a longer run that began earlier
                n = k
                while i + n < len(out) and p + n < len(works[w]) and out[i + n] == works[w][p + n]:
                    n += 1
                if n > best:
                    best, at = n, i
        if best:
            detail.append({"row": row + 1, "spanWords": best, "overLimit": best >= limit, "span": " ".join(out[at:at + min(best, 12)])})
        longest = max(longest, best)
    detail.sort(key=lambda r: -r["spanWords"])
    over = sum(1 for r in detail if r["overLimit"])
    metrics = {"outputs": len(frame), "protectedWorks": len(works), "outputsOverLimit": over, "longestSpanWords": longest, "limitWords": limit}
    summary = (f"No output copies {limit} or more consecutive words from the protected text; the longest shared run is {longest} words." if not over
               else f"{over} of {len(frame)} outputs copy {limit} or more consecutive words from the protected text; the longest run is {longest} words.")
    return result(_verdict(over == 0), summary, metrics, detail)


ENGINES: List[Engine] = [
    Engine(
        id="EV-TST-01",
        method="Accuracy and macro F1 (classification) or MAE, RMSE and R2 (regression) against an agreed baseline and, when given, the last release.",
        slots=(Slot("predictions", "Predictions", "CSV with the true value and the model's prediction per row."),),
        params=(
            Param("y_true", "True value column", "Column holding the correct label or value.", default="y_true"),
            Param("y_pred", "Prediction column", "Column holding the model output.", default="y_pred"),
            Param("task", "Task", "classification or regression.", default="classification"),
            Param("baseline", "Agreed baseline", "Accuracy as 0-1 (classification) or MAE (regression). Required for a verdict.", "number", required=True),
            Param("last_release", "Last release", "The same metric for the previous release. Blank skips the comparison.", "number"),
            Param("max_drop", "Largest drop", "Accuracy points lost, or the relative MAE increase, allowed against the last release.", "number", 0.02),
        ),
        run=task_accuracy,
    ),
    Engine(
        id="EV-TST-02",
        method="A prompt is consistent when every pair of its answers matches after normalising or has TF-IDF cosine similarity at or above the threshold.",
        slots=(Slot("answers", "Answers", "CSV with several answers per prompt."),),
        params=(
            Param("prompt_column", "Prompt column", "Column identifying the prompt.", default="prompt"),
            Param("answer_column", "Answer column", "Column holding each answer.", default="answer"),
            Param("similarity", "Similarity", "Smallest cosine similarity for two answers to agree.", "number", 0.8),
            Param("min_consistent", "Minimum consistent share", "Share of prompts that must be consistent.", "number", 0.9),
        ),
        run=answer_consistency,
    ),
    Engine(
        id="EV-TST-07",
        method="Expected calibration error: the count-weighted mean gap between average score and observed rate across equal-width probability bins.",
        slots=(Slot("predictions", "Predictions", "CSV with the true 0/1 outcome and the predicted probability."),),
        params=(
            Param("y_true", "True outcome column", "Column holding 0 or 1.", default="y_true"),
            Param("score", "Score column", "Probability of the positive class, between 0 and 1.", default="score"),
            Param("bins", "Bins", "Number of equal-width bins.", "number", 10),
            Param("max_ece", "Largest ECE", "The run passes at or below this error.", "number", 0.05),
        ),
        run=calibration,
    ),
    Engine(
        id="EV-TST-08",
        method="AUROC of the out-of-distribution score against the in/out labels, and the false positive rate at 95% true positive rate.",
        slots=(Slot("scores", "Scores", "CSV with an out-of-distribution score and a 0/1 label per row."),),
        params=(
            Param("score", "Score column", "Higher means more out-of-distribution.", default="score"),
            Param("is_ood", "Out-of-distribution column", "1 for out-of-distribution rows, 0 otherwise.", default="is_ood"),
            Param("min_auroc", "Agreed minimum AUROC", "The run passes at or above this AUROC. Required for a verdict.", "number", required=True),
        ),
        run=ood_detection,
    ),
    Engine(
        id="EV-TST-10",
        method="Accuracy per language over languages with enough rows; the gap is the best minus the worst.",
        slots=(Slot("predictions", "Predictions", "CSV with the true label, the prediction and the language per row."),),
        params=(
            Param("y_true", "True label column", "Column holding the correct label.", default="y_true"),
            Param("y_pred", "Prediction column", "Column holding the model output.", default="y_pred"),
            Param("language", "Language column", "Column naming the language of each row.", default="language"),
            Param("max_gap", "Largest gap", "Accuracy gap allowed between best and worst language.", "number", 0.05),
            Param("min_rows", "Minimum rows", "Languages with fewer rows are listed but not compared.", "number", 30),
        ),
        run=multilingual_parity,
    ),
    Engine(
        id="EV-TST-11",
        method="Accuracy on the most confident share of predictions, with a risk-coverage curve at 10% steps.",
        slots=(Slot("predictions", "Predictions", "CSV with the true label, the prediction and the model's confidence."),),
        params=(
            Param("y_true", "True label column", "Column holding the correct label.", default="y_true"),
            Param("y_pred", "Prediction column", "Column holding the model output.", default="y_pred"),
            Param("confidence", "Confidence column", "Column holding the model's confidence; higher is more confident.", default="confidence"),
            Param("coverage", "Coverage", "Share of records the model answers, most confident first.", "number", 0.8),
            Param("min_accuracy", "Agreed minimum accuracy", "Selective accuracy must reach this. Required for a verdict.", "number", required=True),
        ),
        run=selective_accuracy,
    ),
    Engine(
        id="EV-FAI-03",
        method="Selection rate, and true positive rate when labels are given, for every intersection of the attributes with enough records; the gap is the highest minus the lowest.",
        slots=(Slot("decisions", "Decisions", "CSV with the model decision and the protected attributes per row."),),
        params=(
            Param("attributes", "Attributes", "Two or more columns to intersect, comma-separated.", required=True),
            Param("y_pred", "Decision column", "Column holding the model decision.", default="y_pred"),
            Param("y_true", "True label column", "Optional. Adds the true positive rate gap.", default=None),
            Param("favorable", "Favourable value", "The decision value that counts as favourable.", default=1),
            Param("max_gap", "Largest gap", "Largest allowed gap in selection rate (and true positive rate).", "number", 0.1),
            Param("min_slice", "Minimum slice size", "Intersections with fewer records are listed but skipped.", "number", 30),
        ),
        run=intersectional_slices,
    ),
    Engine(
        id="EV-FAI-04",
        method="Flip rate: the share of counterfactual pairs whose predictions differ.",
        slots=(Slot("pairs", "Pairs", "CSV with the original and counterfactual predictions per row, or one row per pair member with a pair id."),),
        params=(
            Param("original_column", "Original column", "Wide format: prediction on the original record.", default="original"),
            Param("counterfactual_column", "Counterfactual column", "Wide format: prediction after changing the protected attribute.", default="counterfactual"),
            Param("pair_column", "Pair column", "Long format: column identifying the pair.", default="pair_id"),
            Param("prediction_column", "Prediction column", "Long format: column holding the prediction.", default="prediction"),
            Param("max_flip_rate", "Largest flip rate", "Share of pairs allowed to change prediction.", "number", 0.02),
        ),
        run=counterfactual_fairness,
    ),
    Engine(
        id="EV-MON-01",
        method="Relative drop of accuracy or macro F1 in production against a baseline file or an agreed baseline value.",
        slots=(
            Slot("production", "Production outcomes", "CSV with the true outcome and the model's prediction in production."),
            Slot("baseline", "Baseline outcomes", "Optional CSV in the same shape from the baseline period.", required=False),
        ),
        params=(
            Param("y_true", "True value column", "Column holding the correct label.", default="y_true"),
            Param("y_pred", "Prediction column", "Column holding the model output.", default="y_pred"),
            Param("metric", "Metric", "accuracy or f1 (macro).", default="accuracy"),
            Param("baseline_value", "Baseline value", "Used when no baseline file is given.", "number"),
            Param("max_relative_drop", "Largest relative drop", "(baseline - current) / baseline allowed.", "number", 0.05),
        ),
        run=production_degradation,
    ),
    Engine(
        id="EV-PRV-02",
        method="AUROC of the model's confidence at telling training records from held-out ones, reported as max(auc, 1 - auc).",
        slots=(Slot("attack", "Attack scores", "CSV with the model's confidence on known members and non-members."),),
        params=(
            Param("score", "Score column", "The model's confidence for each record.", default="score"),
            Param("is_member", "Member column", "1 for training records, 0 for non-members.", default="is_member"),
            Param("max_auc", "Largest AUC", "The run passes at or below this attack AUC.", "number", 0.6),
        ),
        run=membership_inference,
    ),
    Engine(
        id="EV-LEG-01",
        method="Longest run of consecutive words each output shares with any protected work, found by hashing word n-grams.",
        slots=(
            Slot("outputs", "Model outputs", "CSV with one generated text per row."),
            Slot("protected", "Protected text", "UTF-8 text of the protected works; separate works with a line containing only ---.", kind="text"),
        ),
        params=(
            Param("text_column", "Output column", "Column holding the generated text.", default="output"),
            Param("limit_words", "Word limit", "An output fails when it copies this many consecutive words or more.", "number", 50),
        ),
        run=verbatim_reproduction,
    ),
]
