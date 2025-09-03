import logging.config
import pathlib

# Server
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 7878

# Logging
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard'
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
        'propagate': False
    }
}

# Paths
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
ADJECTIVES_PATH = ROOT_DIR / 'resources' / 'adjectives.txt'
NOUNS_PATH = ROOT_DIR / 'resources' / 'nouns.txt'


def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)
