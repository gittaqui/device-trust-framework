import json
from pathlib import Path

from src.lanl_2017_host_adapter import (
    StreamingHostFeatureExtractor,
    parse_host_event,
    summarize,
)


def _event(**kwargs):
    base = {"Time": 2, "EventID": 4624, "UserName": "User1", "Computer": "Comp1"}
    base.update(kwargs)
    return json.dumps(base)


def test_parse_official_schema_fields():
    event = parse_host_event(
        '{"EventID": 4769, "UserName": "User624729", "ServiceName": "Comp883934$", '
        '"DomainName": "Domain002", "Status": "0x0", "Source": "Comp309534", '
        '"Computer": "ActiveDirectory", "Time": 2}'
    )
    assert event.event_id == 4769
    assert event.user == "User624729"
    assert event.computer == "ActiveDirectory"
    assert event.auth_success is True


def test_new_user_host_edge_is_history_based():
    extractor = StreamingHostFeatureExtractor()
    first = extractor.transform(parse_host_event(_event()))
    second = extractor.transform(parse_host_event(_event(Time=3)))
    moved = extractor.transform(parse_host_event(_event(Time=4, Computer="Comp2")))

    assert first["new_user_host_edge"] == 1
    assert second["new_user_host_edge"] == 0
    assert moved["new_user_host_edge"] == 1


def test_prior_failure_reduces_identity_assurance():
    extractor = StreamingHostFeatureExtractor()
    failed = extractor.transform(parse_host_event(_event(EventID=4625)))
    after_failure = extractor.transform(parse_host_event(_event(Time=3, EventID=4624)))

    assert failed["prior_failure_rate"] == 0.0
    assert after_failure["prior_failure_rate"] == 1.0
    assert after_failure["identity_assurance"] < 1.0


def test_process_novelty_is_history_based():
    extractor = StreamingHostFeatureExtractor()
    line = json.dumps(
        {
            "Time": 5,
            "EventID": 4688,
            "UserName": "User1",
            "Computer": "Comp1",
            "ProcessName": "procA.exe",
        }
    )
    first = extractor.transform(parse_host_event(line))
    second = extractor.transform(parse_host_event(line.replace('"Time": 5', '"Time": 6')))

    assert first["new_process_on_host"] == 1
    assert second["new_process_on_host"] == 0


def test_bounded_summary(tmp_path: Path):
    path = tmp_path / "wls_sample.jsonl"
    path.write_text(
        "\n".join(
            [
                _event(),
                _event(Time=3, EventID=4625),
                json.dumps(
                    {
                        "Time": 4,
                        "EventID": 4688,
                        "UserName": "User1",
                        "Computer": "Comp1",
                        "ProcessName": "procA.exe",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = summarize(path, max_rows=3)
    assert result["processed"] == 3
    assert result["auth_failures"] == 1
    assert result["process_starts"] == 1
