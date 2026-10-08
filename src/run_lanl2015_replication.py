"""Execute the frozen LANL-2015 replication (red-team rows 26–50).

Controls are unlabeled times, never verified benign. This wrapper preserves the
13 frozen features in extract_lanl_paired_context_remote.py. No outcomes are
inspected in control selection, and the target cohort is never re-optimized.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path

from extract_lanl_paired_context_remote import FROZEN_FEATURES, extract_paired_features
from prepare_lanl2015_remote import download_redteam, parse_redteam
from select_lanl2015_replication_controls import build_replication_manifest

LABEL_START = 25
LABEL_COUNT = 25
WINDOW_RADIUS_SECONDS = 600
FROZEN_PROTOCOL = "experiments/lanl-2015-second-cohort-replication-freeze.md"
PRIMARY_FEATURES = ("proc_event_count", "proc_unique_process_count", "proc_start_count")


def prepare_replication(redteam_text: str) -> tuple[str, dict[str, object]]:
    """Select frozen labels/controls from the complete unmodified label stream."""
    all_labels = parse_redteam(io.StringIO(redteam_text))
    if len(all_labels) < LABEL_START + LABEL_COUNT:
        raise ValueError("frozen replication requires at least 50 red-team rows")
    manifest = build_replication_manifest(
        all_labels,
        label_start=LABEL_START,
        label_limit=LABEL_COUNT,
        radius_seconds=WINDOW_RADIUS_SECONDS,
    )
    if manifest["protocol"] != FROZEN_PROTOCOL:
        raise ValueError("unexpected preregistration protocol")
    if len(manifest["controls"]) != LABEL_COUNT:
        raise ValueError("frozen controls have an incorrect cohort count")
    # The extractor consumes the supplied red-team text as a cohort-local slice,
    # so it does not need a mutable or outcome-dependent cohort-start argument.
    selected_text = "".join(
        f"{event.time},{event.user},{event.source_computer},{event.destination_computer}\n"
        for event in all_labels[LABEL_START:LABEL_START + LABEL_COUNT]
    )
    return selected_text, manifest


def execute_replication(
    *, redteam_text: str, control_manifest_path: Path,
    output_csv: Path, summary_json: Path, repo_id: str = "Taqui/lanl-cyber-datasets",
    readers=None, preflight_only: bool = False,
) -> dict[str, object]:
    """Write frozen manifest, then (unless preflight) read paired telemetry."""
    selected_text, manifest = prepare_replication(redteam_text)
    control_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    control_manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    provenance = {
        "original_redteam_label_sha256": hashlib.sha256(
            redteam_text.encode("utf-8")
        ).hexdigest(),
        "frozen_protocol": FROZEN_PROTOCOL,
        "original_redteam_row_start_one_based": 26,
        "original_redteam_row_end_one_based_inclusive": 50,
        "candidate_offsets_seconds": manifest["candidate_offsets_seconds"],
        "preflight_only": preflight_only,
        "control_semantics": manifest["control_semantics"],
    }
    if preflight_only:
        return {"status": "preflight_only", "provenance": provenance, "matched_pair_count": manifest["matched_count"]}
    if len(FROZEN_FEATURES) != 13 or not set(PRIMARY_FEATURES).issubset(FROZEN_FEATURES):
        raise RuntimeError("extractor feature schema diverged from frozen design")
    summary = extract_paired_features(
        repo_id=repo_id,
        redteam_path="lanl-2015/redteam.txt",
        control_manifest_path=control_manifest_path,
        output_csv=output_csv,
        summary_json=summary_json,
        label_limit=LABEL_COUNT,
        radius_seconds=WINDOW_RADIUS_SECONDS,
        redteam_text=selected_text,
        control_manifest=manifest,
        readers=readers,
        token=os.getenv("HF_TOKEN"),
    )
    if summary["frozen_features"] != list(FROZEN_FEATURES):
        raise RuntimeError("unexpected frozen-feature schema in extracted result")
    summary["replication_provenance"] = provenance
    summary["label_index_note"] = "paired CSV target_index is zero-based within the frozen 26–50 cohort"
    summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Frozen second LANL red-team cohort.")
    parser.add_argument("--repo-id", default="Taqui/lanl-cyber-datasets")
    parser.add_argument("--control-manifest", type=Path, default=Path("data/external/lanl-2015/replication-control-manifest.json"))
    parser.add_argument("--output", type=Path, default=Path("data/external/lanl-2015/replication-paired-features.csv"))
    parser.add_argument("--summary", type=Path, default=Path("results/lanl-2015-replication-summary.json"))
    parser.add_argument("--preflight-only", action="store_true", help="freeze controls without reading outcome telemetry")
    args = parser.parse_args()
    redteam_text = download_redteam().read_text(encoding="utf-8")
    result = execute_replication(
        redteam_text=redteam_text,
        control_manifest_path=args.control_manifest,
        output_csv=args.output,
        summary_json=args.summary,
        repo_id=args.repo_id,
        preflight_only=args.preflight_only,
    )
    print(json.dumps(result if args.preflight_only else {
        "matched_pairs": result["matched_pair_count"],
        "unmatched_pairs": result["unmatched_pair_count"],
        "claim_boundary": result["claim_boundary"],
    }, indent=2))


if __name__ == "__main__":
    main()
