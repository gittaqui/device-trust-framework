"""Render frozen LANL second-cohort results into an auditable IEEE LaTeX fragment.

The public, de-identified LANL contextual observations are NOT endpoint
compliance or independently adjudicated benign controls. This script refuses
unrecognized evidence hashes in its CLI to prevent accidental evidence drift.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

EXPECTED_PAIR_SHA256 = "6dfe2e18ed65d2f54d6a73ce5cb8b9848b0ecdf78e3fd36bbf469a52396f14db"
EXPECTED_MANIFEST_SHA256 = "190190ac1b75495fdfb18422da8b727bdac88553852edba8d236fb3d544957ff"
FEATURES = (
    ("proc_event_count", "Process events"),
    ("proc_unique_process_count", "Unique processes"),
    ("proc_start_count", "Process starts"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _count(value: str) -> int:
    number = int(value)
    if number < 0:
        raise ValueError("negative event count")
    return number


def load_and_verify(pairs: Path, manifest: Path, *, require_frozen_hash: bool = True) -> list[dict[str, str]]:
    """Validate paired evidence and control assignments against the frozen manifest."""
    if require_frozen_hash and (sha256(pairs) != EXPECTED_PAIR_SHA256 or sha256(manifest) != EXPECTED_MANIFEST_SHA256):
        raise ValueError("evidence SHA-256 mismatch: do not silently replace frozen inputs")
    with pairs.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"target_index", "target_time", "target_user", "target_source_computer",
                    "target_destination_computer", "matched", "control_time", "offset_seconds"}
        for feature, _ in FEATURES:
            required |= {"target_" + feature, "control_" + feature}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("missing required CSV columns")
        rows = list(reader)
    source = json.loads(manifest.read_text(encoding="utf-8"))
    controls = source.get("controls")
    if (len(rows) != 25 or not isinstance(controls, list) or len(controls) != 25
            or source.get("label_start_zero_based") != 25
            or source.get("target_label_count") != 25
            or source.get("radius_seconds") != 600):
        raise ValueError("frozen cohort or manifest drift")
    if source.get("matched_count") != sum(r["matched"] == "True" for r in rows):
        raise ValueError("manifest matched-count drift")
    if source.get("unmatched_count") != sum(r["matched"] == "False" for r in rows):
        raise ValueError("manifest unmatched-count drift")
    for i, (row, control) in enumerate(zip(rows, controls, strict=True)):
        if int(row["target_index"]) != i or control["target_index"] != i:
            raise ValueError("target index mismatch")
        if row["matched"] not in ("True", "False") or control["matched"] != (row["matched"] == "True"):
            raise ValueError("invalid match flag")
        target = control["target"]
        for column, key in (("target_user", "user"), ("target_source_computer", "source_computer"),
                            ("target_destination_computer", "destination_computer")):
            if row[column] != target[key]:
                raise ValueError("target entity does not match manifest")
        if int(row["target_time"]) != target["time"]:
            raise ValueError("target time does not match manifest")
        for feature, _ in FEATURES:
            _count(row["target_" + feature])
        if row["matched"] == "True":
            offset = int(row["offset_seconds"])
            if offset not in source["candidate_offsets_seconds"]:
                raise ValueError("control offset outside preregistered choices")
            if (int(row["control_time"]) - int(row["target_time"]) != offset
                    or control["control_time"] != int(row["control_time"])
                    or control["offset_seconds"] != offset):
                raise ValueError("control time or offset inconsistent with manifest")
            for feature, _ in FEATURES:
                _count(row["control_" + feature])
        elif row["control_time"] or row["offset_seconds"]:
            raise ValueError("unmatched target unexpectedly has a control")
    return rows


def analyze(rows: list[dict[str, str]]) -> dict:
    """Compute descriptive paired summaries, sharp finite-cohort bounds, and grouping."""
    if len(rows) != 25 or [int(r["target_index"]) for r in rows] != list(range(25)):
        raise ValueError("analysis requires the 25 frozen targets")
    matched = [r for r in rows if r["matched"] == "True"]
    unmatched = [r for r in rows if r["matched"] == "False"]
    if not matched or len(matched) + len(unmatched) != 25:
        raise ValueError("invalid match coverage")
    ordered = sorted(rows, key=lambda r: (int(r["target_time"]), int(r["target_index"])))
    episodes: dict[int, int] = {}
    episode = -1
    previous = None
    for row in ordered:
        time = int(row["target_time"])
        if previous is None or time - previous > 1200:
            episode += 1
        episodes[int(row["target_index"])] = episode
        previous = time
    summaries = {}
    for feature, label in FEATURES:
        targets = [_count(r["target_" + feature]) for r in matched]
        controls = [_count(r["control_" + feature]) for r in matched]
        differences = [t - c for t, c in zip(targets, controls, strict=True)]
        higher = sum(d > 0 for d in differences)
        tied = sum(d == 0 for d in differences)
        lower = sum(d < 0 for d in differences)
        possible_higher = sum(_count(r["target_" + feature]) > 0 for r in unmatched)
        groups = {"user": defaultdict(list), "episode": defaultdict(list)}
        for row, delta in zip(matched, differences, strict=True):
            groups["user"][row["target_user"]].append(delta)
            groups["episode"][episodes[int(row["target_index"])]].append(delta)
        summaries[feature] = {
            "label": label,
            "target_median": statistics.median(targets),
            "control_median": statistics.median(controls),
            "median_paired_difference": statistics.median(differences),
            "higher": higher, "tied": tied, "lower": lower,
            "bound_lower": higher / 25,
            "bound_upper": (higher + possible_higher) / 25,
            "user_groups": len(groups["user"]),
            "user_group_positive_medians": sum(statistics.median(v) > 0 for v in groups["user"].values()),
            "episode_groups": len(groups["episode"]),
            "episode_positive_medians": sum(statistics.median(v) > 0 for v in groups["episode"].values()),
        }
    return {
        "total_targets": 25, "matched": len(matched), "unmatched": len(unmatched),
        "matched_users": len({r["target_user"] for r in matched}),
        "matched_source_hosts": len({r["target_source_computer"] for r in matched}),
        "overlap_episodes_all": len(set(episodes.values())),
        "features": summaries,
    }


def _fmt(value: int | float) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)


def render_tex(result: dict) -> str:
    """Produce a descriptive subsection, without invalid inferential claims."""
    lines = [
        "% Auto-generated by scripts/render_lanl_replication_results.py from frozen public LANL evidence.",
        "% Paired CSV SHA-256: " + EXPECTED_PAIR_SHA256,
        "% Control manifest SHA-256: " + EXPECTED_MANIFEST_SHA256,
        r"\subsection{Frozen Second-Cohort Observations and Missing-Control Sensitivity}",
        "The preregistered LANL second cohort (original red-team rows 26--50)",
        f"contains {result['total_targets']} targets, of which {result['matched']} have eligible temporal controls and",
        f"{result['unmatched']} remain unmatched. Controls are \\emph{{unlabeled}}, not verified benign.",
        "Table~\\ref{tab:lanl-second-frozen} summarizes three prespecified process",
        "features. The median of within-pair differences need not equal the",
        "difference between target and control marginal medians.",
        r"\begin{table}[ht]", r"\centering",
        r"\caption{Frozen LANL second-cohort descriptive comparisons.}",
        r"\label{tab:lanl-second-frozen}",
        r"\begin{tabular}{lrrrr}", r"\toprule",
        r"Feature & T/C medians & Paired $\Delta$ & T$>$C & Bounds \\",
        r"\midrule",
    ]
    for feature, _ in FEATURES:
        item = result["features"][feature]
        medians = f"{_fmt(item['target_median'])}/{_fmt(item['control_median'])}"
        bounds = f"[{item['bound_lower']:.2f},{item['bound_upper']:.2f}]"
        lines.append(f"{item['label']} & {medians} & {_fmt(item['median_paired_difference'])} & {item['higher']}/{result['matched']} & {bounds} \\\\")
    lines.extend([
        r"\bottomrule", r"\end{tabular}", r"\end{table}",
        "The bounds apply only to the 25 selected targets: unmatched controls",
        "have unknown nonnegative process counts. The lower bound treats all",
        "unmatched comparisons as not target-higher; the upper bound counts",
        "an unmatched comparison as potentially target-higher only when its",
        "target count is positive. These are logical finite-cohort bounds,",
        r"\emph{not} confidence intervals or population estimates.",
        f"A post-hoc audit found {result['matched_users']} distinct users and {result['matched_source_hosts']} source computers among",
        f"matched targets and {result['overlap_episodes_all']} overlapping-window episodes in the frozen cohort.",
        "Repeated users, source hosts and overlapping windows preclude treating",
        "pair-level sign-test $p$ values or Wilson intervals as calibrated",
        r"population-level inference \cite{cameron2015cluster}.",
        "The three process features are correlated and do not represent",
        "independent discoveries. The data do not establish attack-detection",
        "accuracy, verified benign controls, causal effects, or the effectiveness",
        "of the proposed eight-factor device-trust access model. Independent",
        "endpoint-posture measurements and adjudicated access outcomes remain",
        "necessary before external effectiveness claims.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rows = load_and_verify(args.pairs, args.manifest)
    result = analyze(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_tex(result), encoding="utf-8")
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
