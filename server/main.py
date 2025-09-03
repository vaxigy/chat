import logging

from core.infrastructure.adapters.websocket import (
    WebSocketServer,
    WebSocketBroadcaster
)
from core.infrastructure.adapters.word_id import WordIDGenerator
from core.config import SERVER_HOST, SERVER_PORT, LOGGER_CONFIG
from core.application.runner import ChatRunner


def main():
    logger = logging.getLogger('chat_server')
    handler = logging.StreamHandler()
    format = logging.Formatter(LOGGER_CONFIG['format'])
    handler.setFormatter(format)
    logger.addHandler(handler)
    logger.setLevel(LOGGER_CONFIG['level'])
    
    server = WebSocketServer()
    broadcaster = WebSocketBroadcaster()
    id_generator = WordIDGenerator()
    
    runner = ChatRunner(
        SERVER_HOST,
        SERVER_PORT,
        server,
        logger,
        broadcaster,
        id_generator
    )
    runner.run()


if __name__ == '__main__':
    main()
