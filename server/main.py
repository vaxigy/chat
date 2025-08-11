from core.runner import ChatRunner
from core.config import SERVER_HOST, SERVER_PORT

if __name__ == '__main__':
    server = ChatRunner(SERVER_HOST, SERVER_PORT)
    server.run()
