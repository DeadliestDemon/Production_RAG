import json
import logging

from app.monitoring import JSONFormatter, MetricsCollector, RequestTimer, get_logger


def test_json_formatter_includes_expected_fields():
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="demo",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello world",
        args=(),
        exc_info=None,
    )
    record.funcName = "test_json_formatter_includes_expected_fields"

    payload = json.loads(formatter.format(record))

    assert payload["level"] == "INFO"
    assert payload["message"] == "hello world"
    assert payload["module"] == "test_monitoring"
    assert payload["function"] == "test_json_formatter_includes_expected_fields"


def test_json_formatter_includes_extra_data():
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="demo",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    record.funcName = "test_json_formatter_includes_extra_data"
    record.extra_data = {"request_id": "abc123"}

    payload = json.loads(formatter.format(record))

    assert payload["request_id"] == "abc123"


def test_metrics_collector_tracks_requests_error_and_cache_state():
    collector = MetricsCollector()

    collector.record_request(12.5, input_tokens=10, output_tokens=6, error=True, cache_hit=True)
    collector.record_request(20.0, input_tokens=4, output_tokens=2, error=False, cache_hit=False)

    summary = collector.summary

    assert summary["total_requests"] == 2
    assert summary["total_errors"] == 1
    assert summary["error_rate"] == "0.50"
    assert summary["avg_latency_ms"] == 16.25
    assert summary["cache_hit_rate"] == "0.50"
    assert summary["total_input_tokens"] == 14
    assert summary["total_output_tokens"] == 8


def test_metrics_collector_handles_no_requests():
    collector = MetricsCollector()

    summary = collector.summary

    assert summary["total_requests"] == 0
    assert summary["total_errors"] == 0
    assert summary["error_rate"] == "0.00"
    assert summary["avg_latency_ms"] == 0.0
    assert summary["cache_hit_rate"] == "0.00"
    assert summary["total_input_tokens"] == 0
    assert summary["total_output_tokens"] == 0


def test_request_timer_records_elapsed_time():
    timer = RequestTimer()

    with timer:
        pass

    assert timer.elapsed_ms >= 0


def test_get_logger_returns_logger_with_handler():
    logger = get_logger("unit-test-logger")

    assert logger.name == "unit-test-logger"
    assert logger.level == logging.INFO
    assert logger.handlers
