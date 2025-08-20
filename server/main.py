from core.runner import ChatRunner
from core.config import SERVER_HOST, SERVER_PORT


def main():
    server = ChatRunner(SERVER_HOST, SERVER_PORT)
    server.run()


if __name__ == '__main__':
    main()
