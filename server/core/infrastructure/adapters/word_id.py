import random

from core.domain.ports import IDGenerator
from core.config import ADJECTIVES_PATH, NOUNS_PATH


class WordIDGenerator(IDGenerator):
    """
    Word-based ID generator.
    
    The class handles the data loading
    needed for generation, and the generation logic.
    
    Supports one ID pattern: `adjective-noun-number`,
    where `adjective` and `noun` are the random words from
    the provided sources, and `number` is a random sequence of digits.
    """
    def __init__(
        self,
        adjectives_path: str = ADJECTIVES_PATH,
        nouns_path: str = NOUNS_PATH,
        number_len: int = 3,
    ) -> None:
        """
        Construct an ID generator from the source files.
        
        Args:
            adjectives_path (str): Path to the file with adjectives.
            nouns_path (str): Path to the file with nouns.
            number_len (int): Length of the suffix number.
        """
        self._adjectives: list[str] = self._load_file(adjectives_path)
        self._nouns: list[str] = self._load_file(nouns_path)
        self._digits: str = '0123456789'
        self._number_len: int = number_len
    
    def _load_file(self, path: str) -> list[str]:
        with open(path) as file:
            return [line.strip() for line in file if line.strip()]
    
    def generate_id(self) -> str:
        """
        Generate a random word-based ID.
        """
        adjective = random.choice(self._adjectives)
        noun = random.choice(self._nouns)
        number = ''.join(
            random.choice(self._digits)
            for _ in range(self._number_len)
        )
        return f'{adjective}-{noun}-{number}'
