import logging
import pathlib

# Server
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 7878

# Logger
LOGGER_CONFIG = {
    'level': logging.INFO,
    'format': '%(asctime)s [%(levelname)s] - %(message)s',
    'datefmt': '%Y-%m-%d %H:%M:%S'
}

# Paths
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
ADJECTIVES_PATH = ROOT_DIR / 'data' / 'adjectives.txt'
NOUNS_PATH = ROOT_DIR / 'data' / 'nouns.txt'
