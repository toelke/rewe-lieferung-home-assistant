import logging
import os
import sys
import threading

import structlog

logging_setup_called = False


def setup_logging(name="<app>", level=None):
    """
    Setup logging. Returns a struct-logger.

    Usage:
    ```
    log = setup_logging()
    log.warn("This is a warning!", some_value=679)
    ```
    """
    global logging_setup_called
    if logging_setup_called:
        return structlog.getLogger(name)

    log_level = os.environ.get("LOG_LEVEL", "INFO" if level is None else level)
    # Use nice colorful formatting for TTYs, use JSON output otherwise
    do_json = not sys.stdout.isatty()

    # Build list of structlog processors to apply to log messages
    processors = [
        # Set up event dict to contain relevant vars
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.ExtraAdder(),
        # Add log level and name
        structlog.processors.add_log_level,
        structlog.stdlib.add_logger_name,
        # Add exception info
        structlog.dev.set_exc_info,
        structlog.processors.StackInfoRenderer(),
    ]
    if do_json:
        processors.append(structlog.processors.dict_tracebacks)
        # Add timestamps, only for JSON output
        processors.append(structlog.processors.TimeStamper(fmt="iso", utc=True, key="ts"))

    # Configure structlog loggers to apply processors and send result to the Logging module
    structlog.configure(
        processors=processors + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure structlog formatter to apply processors to messages that originate from a Logging module
    # logger, then remove internal metadata, and then display the message as JSON or nicely formatted.
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer() if do_json else structlog.dev.ConsoleRenderer(),
        ],
    )

    # Configure Logging module to send messages (either from Logging loggers or structlog loggers) to
    # the structlog formatter.
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    rootLogger = logging.getLogger()
    rootLogger.addHandler(handler)
    rootLogger.setLevel(logging.getLevelName(log_level))

    # Handle uncaught exceptions
    def handle_uncaught(type, value, traceback):
        logging.critical("Uncaught exception", exc_info=(type, value, traceback))

    def handle_uncaught_thread(args):
        if args.exc_type == SystemExit:
            return
        handle_uncaught(args.exc_type, args.exc_value, args.exc_traceback)

    sys.excepthook = handle_uncaught
    threading.excepthook = handle_uncaught_thread

    # Remember that we're done here.
    logging_setup_called = True

    return structlog.getLogger(name)
