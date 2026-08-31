from src.utils import logging


def test_logging_processors_and_context():
    event = logging.rename_event_key(None, None, {"event": "hello"})
    assert event == {"message": "hello"}
    logging.init_logger_context("request-1")
    assert logging.get_context()["request_id"] == "request-1"
    logging.bind_context(user_id="u")
    assert logging.get_context()["user_id"] == "u"
    logging.clear_context()
    assert logging.get_context() == {}
    assert logging.get_logger("tests") is not None
    logging.configure_default_loggers([])
    logging.configure_logger(["tests"])
