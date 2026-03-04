from pathlib import Path

from app.services.openclaw.common.errors import (
    DispatchErrorType,
    DispatchException,
    DispatchPhase,
    TaskParsingError,
)
from app.services.openclaw.observability.dispatch_metrics import DispatchMetrics
from scripts.migrate_openclaw_layout import run


def _counter_value(counter, labels):
    for sample in counter.collect()[0].samples:
        if sample.name.endswith("_total") and all(sample.labels.get(k) == v for k, v in labels.items()):
            return sample.value
    return 0.0


def test_dispatch_exception_fields():
    exc = DispatchException(
        DispatchErrorType.ROUTING_INVALID,
        "bad routing",
        http_status=403,
        error_code="OPENCLAW_ROUTING_SIGNATURE_INVALID",
    )
    assert exc.error_type == DispatchErrorType.ROUTING_INVALID
    assert exc.http_status == 403
    assert exc.error_code == "OPENCLAW_ROUTING_SIGNATURE_INVALID"
    assert str(exc) == "bad routing"


def test_task_parsing_error_fields():
    exc = TaskParsingError("{}", "schema", retry_count=2)
    assert exc.raw_response == "{}"
    assert exc.validation_error == "schema"
    assert exc.retry_count == 2
    assert "schema" in str(exc)


def test_dispatch_phase_values():
    assert DispatchPhase.WS_SEND.value == "WS_SEND"
    assert DispatchPhase.HTTP_RESP.value == "HTTP_RESP"


def test_dispatch_metrics_increment():
    from app.services.openclaw.observability.dispatch_metrics import DISPATCH_FAIL_REASON, DISPATCH_TOTAL

    before_total = _counter_value(DISPATCH_TOTAL, {"status": "success"})
    before_fail = _counter_value(DISPATCH_FAIL_REASON, {"reason": "demo_reason"})

    DispatchMetrics.record_dispatch("success")
    DispatchMetrics.record_fail_reason("demo_reason")

    after_total = _counter_value(DISPATCH_TOTAL, {"status": "success"})
    after_fail = _counter_value(DISPATCH_FAIL_REASON, {"reason": "demo_reason"})

    assert after_total == before_total + 1
    assert after_fail == before_fail + 1


def test_dispatch_metrics_latency_observe():
    DispatchMetrics.observe_latency(0.0)


def test_migration_script_dry_run_and_apply(tmp_path: Path):
    py_file = tmp_path / "demo.py"
    py_file.write_text(
        "from app.services.openclaw.exceptions import DispatchException\n"
        "from app.services.openclaw.metrics import DispatchMetrics\n",
        encoding="utf-8",
    )
    scanned, changed = run(tmp_path, dry_run=True)
    assert scanned >= 1
    assert changed == 1
    assert "openclaw.exceptions" in py_file.read_text(encoding="utf-8")

    scanned_apply, changed_apply = run(tmp_path, dry_run=False)
    assert scanned_apply >= 1
    assert changed_apply == 1
    rewritten = py_file.read_text(encoding="utf-8")
    assert "app.services.openclaw.common.errors" in rewritten
    assert "app.services.openclaw.observability.dispatch_metrics" in rewritten
