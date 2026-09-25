import json

from src.lanl_2017_host_adapter import StreamingHostFeatureExtractor, parse_host_event
from src.evaluate_lanl_2017_fast import FastState


def test_fast_state_matches_frozen_adapter_on_representative_sequence():
    rows = [
        {"UserName": "u1", "EventID": 4624, "LogHost": "h1", "Time": 1},
        {"UserName": "u1", "EventID": 4625, "LogHost": "h2", "Time": 2},
        {"UserName": "u1", "EventID": 4648, "LogHost": "h2", "Time": 3},
        {"UserName": "u2", "EventID": 4672, "LogHost": "h3", "Time": 4},
        {"UserName": "u1", "EventID": 4688, "LogHost": "h1", "ProcessName": "p.exe", "Time": 5},
        {"UserName": "u1", "EventID": 4688, "LogHost": "h1", "ProcessName": "p.exe", "Time": 6},
        {"UserName": "u1", "EventID": 4769, "LogHost": "h1", "Status": "0x1", "Time": 7},
    ]

    frozen = StreamingHostFeatureExtractor()
    fast = FastState()

    for raw in rows:
        expected = frozen.transform(parse_host_event(json.dumps(raw)))
        actual = fast.transform(raw)
        for field in (
            "identity_assurance",
            "anomaly_risk",
            "freshness",
            "new_user_host_edge",
            "explicit_credentials",
            "privileged_logon",
            "new_process_on_host",
        ):
            assert actual[field] == expected[field]
