import logging
import structlog
from uuid import uuid4
from typing import Any, Optional
from structlog.types import EventDict, Processor


def get_logger(logger_name: str = "app") -> structlog.BoundLogger:
    """
    Get a logger instance with the specified name.

    Args:
        logger_name (str): The name of the logger. Default is "app".

    Returns:
        structlog.BoundLogger: A configured logger instance.
    """
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
    )

    return structlog.stdlib.get_logger(logger_name)


def rename_event_key(logger, method_name, event_dict: EventDict) -> EventDict:
    """
    Rename the 'event' key in the log record to 'message'.

    Args:
        _: Unused parameter (logger).
        __: Unused parameter (method_name).
        event_dict (EventDict): The log record as a dictionary.
    Returns:
        EventDict: The modified log record with 'message' key instead of 'event'.
    """
    if "event" in event_dict:
        event_dict["message"] = event_dict.pop("event")
    return event_dict


def __get_processors() -> list[Processor]:
    """
    Get the list of processors for structlog configuration.

    Returns:
        list[Processor]: A list of processors to be used in structlog configuration.
    """
    return [
        rename_event_key,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.PATHNAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
    ]


def configure_logger(default_logger_names: Optional[list[str]] = None):
    structlog.configure(
        processors=__get_processors()
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )
    if default_logger_names:
        configure_default_loggers(default_logger_names)


def configure_default_loggers(logger_names: list[str]):
    if not logger_names:
        return

    handler = logging.StreamHandler()
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=__get_processors(),
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )
    handler.setFormatter(formatter)
    for logger_name in logger_names:
        if logger_name in ["uvicorn.access", "uvicorn.error", "uvicorn"]:
            logging.getLogger(logger_name).handlers.clear()
            logging.getLogger(logger_name).propagate = "access" not in logger_name
            continue
        lgr = (
            logging.getLogger()
            if (logger_name in ["root", ""])
            else logging.getLogger(logger_name)
        )
        lgr.handlers.clear()
        lgr.addHandler(handler)
        lgr.setLevel(logging.INFO)


def bind_context(**kwargs: Any) -> None:
    """
    Initialize the logger context with the provided keyword arguments.

    Args:
        **kwargs: Arbitrary keyword arguments to be added to the logger context.
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """
    Clear the logger context, removing all bound variables.
    """
    structlog.contextvars.clear_contextvars()


def init_logger_context(request_id: Optional[str] = None) -> None:
    """
    Initialize the logger context with the provided keyword arguments.

    Args:
        **kwargs: Arbitrary keyword arguments to be added to the logger context.
    """
    clear_context()
    bind_context(request_id=request_id or uuid4().hex)


def get_context() -> dict[str, Any]:
    """
    Get the current logger context as a dictionary.

    Returns:
        dict[str, Any]: The current logger context.
    """
    return structlog.contextvars.get_contextvars()
