import logging

from core.application.runner import ChatRunner
from core.config import SERVER_HOST, SERVER_PORT, LOGGER_CONFIG


def main():
    logger = logging.getLogger('chat_server')
    handler = logging.StreamHandler()
    format = logging.Formatter(LOGGER_CONFIG['format'])
    handler.setFormatter(format)
    logger.addHandler(handler)
    logger.setLevel(LOGGER_CONFIG['level'])
    
    runner = ChatRunner(
        SERVER_HOST,
        SERVER_PORT,
        logger
    )
    runner.run()


if __name__ == '__main__':
    main()
