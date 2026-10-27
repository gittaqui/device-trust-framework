"""Idempotently replace the outdated pending-result paragraph in paper/main.tex.

Run only after checking that the generated fragment matches frozen evidence.
Refuses unexpected manuscript structure rather than deleting unrelated prose.
"""
from __future__ import annotations

import argparse
from pathlib import Path

START = r"\textbf{Replication status at the time of drafting:}"
NEXT = r"\section{Threats to Validity}"
INPUT = r"\input{lanl-second-cohort-auto}"
CURRENT_ROOT_INPUT = r"\input{lanl-second-cohort-auto.tex}"
CURRENT_FALLBACK_INPUT = r"\input{paper/lanl-second-cohort-auto.tex}"
CURRENT_GUARD = r"\IfFileExists{lanl-second-cohort-auto.tex}"


def integrate(manuscript: str) -> str:
    # Both the historical single include and the current two-path
    # IfFileExists wrapper are valid integrated states.
    counts = (manuscript.count(INPUT), manuscript.count(CURRENT_ROOT_INPUT),
              manuscript.count(CURRENT_FALLBACK_INPUT), manuscript.count(CURRENT_GUARD))
    if any(counts):
        if START in manuscript:
            raise ValueError("both old and new replication sections present")
        if counts not in ((1, 0, 0, 0), (0, 1, 1, 1)):
            raise ValueError("duplicate or incomplete replication input")
        return manuscript
    start = manuscript.find(START)
    if start < 0:
        raise ValueError("expected stale status paragraph not found; inspect manuscript manually")
    end = manuscript.find(NEXT, start)
    if end < 0:
        raise ValueError("expected threats-to-validity section not found")
    old = manuscript[start:end]
    if "outcome is not reported here pending verified workflow artifacts" not in old:
        raise ValueError("status paragraph changed; manual reconciliation required")
    return manuscript[:start] + INPUT + "\n\n" + manuscript[end:]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manuscript", type=Path, default=Path("paper/main.tex"))
    parser.add_argument("--fragment", type=Path, default=Path("paper/lanl-second-cohort-auto.tex"))
    args = parser.parse_args()
    if not args.fragment.exists():
        raise FileNotFoundError("render the frozen replication fragment before integrating")
    original = args.manuscript.read_text(encoding="utf-8")
    revised = integrate(original)
    if revised != original:
        args.manuscript.write_text(revised, encoding="utf-8")
        print("updated manuscript with generated replication results")
    else:
        print("already integrated; no change")


if __name__ == "__main__":
    main()
