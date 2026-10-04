"""Frozen same-weekday controls for LANL-2015 replication rows 26-50."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from prepare_lanl2015_remote import download_redteam, merge_windows, parse_redteam, RedTeamEvent
from select_lanl2015_controls import select_controls

REPLICATION_OFFSETS_SECONDS=(604800,1209600,1814400,-604800,-1209600,-1814400)

def build_replication_manifest(all_redteam:list[RedTeamEvent], *, label_start:int=25, label_limit:int=25, radius_seconds:int=600)->dict[str,object]:
    if label_start<0 or label_limit<1 or radius_seconds<0: raise ValueError("invalid cohort parameters")
    targets=all_redteam[label_start:label_start+label_limit]
    if len(targets)!=label_limit: raise ValueError("insufficient red-team rows")
    controls=select_controls(targets,all_redteam,radius_seconds=radius_seconds,offsets=REPLICATION_OFFSETS_SECONDS)
    matched=[x for x in controls if x["matched"]]
    pseudo=[RedTeamEvent(int(x["control_time"]),"","","") for x in matched]
    return {
      "dataset":"LANL Comprehensive Multi-Source Cyber-Security Events (2015)",
      "authoritative_doi":"10.17021/1179829",
      "protocol":"experiments/lanl-2015-second-cohort-replication-freeze.md",
      "label_start_zero_based":label_start,"target_label_count":len(targets),
      "redteam_rows_used_for_exclusion":len(all_redteam),"radius_seconds":radius_seconds,
      "candidate_offsets_seconds":list(REPLICATION_OFFSETS_SECONDS),
      "matched_count":len(matched),"unmatched_count":len(controls)-len(matched),
      "controls":controls,
      "merged_control_windows":[list(x) for x in merge_windows(pseudo,radius_seconds,radius_seconds)],
      "control_semantics":"matched non-red-team same-weekday temporal controls; unlabeled and not verified benign",
      "research_warning":"Absence from redteam.txt does not establish benignness; do not compute false-positive rates."
    }

def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument("--output",type=Path,default=Path("data/external/lanl-2015/replication-control-manifest.json"))
    args=ap.parse_args(); path=download_redteam()
    with path.open("r",encoding="utf-8",newline="") as h: events=parse_redteam(h)
    m=build_replication_manifest(events); args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(m,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"matched":m["matched_count"],"unmatched":m["unmatched_count"]}))
if __name__=="__main__": main()
