import logging

from core.infrastructure.adapters.websocket import (
    WebSocketServer,
    WebSocketBroadcaster
)
from core.infrastructure.adapters.word_id import WordIDGenerator
from core.config import SERVER_HOST, SERVER_PORT, setup_logging
from core.application.runner import ChatRunner


def main():
    setup_logging()
    logger = logging.getLogger('chat_server')
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
