"""Load Hangman word lists and choose a word by difficulty.

This module does not depend on Flask or a user interface. The game
engine still receives a single word and applies the rules itself.
"""

from __future__ import annotations

import random
from pathlib import Path


DIFFICULTIES = ("easy", "medium", "hard")


class InvalidDifficultyError(ValueError):
    """The requested difficulty is not easy, medium, or hard."""


class InvalidWordListError(ValueError):
    """A word list is missing, empty, or contains a non-alphabetic entry."""


class WordManager:
    """Words for the three public difficulty levels."""

    def __init__(self, words_dir: Path | str | None = None) -> None:
        self._words_dir = (
            Path(words_dir) if words_dir is not None else _default_words_dir()
        )
        self._lists = {
            difficulty: _load_word_list(self._words_dir / f"{difficulty}.txt")
            for difficulty in DIFFICULTIES
        }

    def words(self, difficulty: str) -> tuple[str, ...]:
        """Return the words for one difficulty, in file order."""
        return self._lists[_normalize_difficulty(difficulty)]

    def random_word(
        self,
        difficulty: str,
        rng: random.Random | None = None,
    ) -> str:
        """Return one word from the requested difficulty."""
        choices = self.words(difficulty)
        picker = rng if rng is not None else random
        return picker.choice(choices)


def _default_words_dir() -> Path:
    return Path(__file__).resolve().parent / "words"


def _normalize_difficulty(difficulty: str) -> str:
    if not isinstance(difficulty, str):
        raise InvalidDifficultyError("difficulty must be easy, medium, or hard")
    normalized = difficulty.strip().lower()
    if normalized not in DIFFICULTIES:
        raise InvalidDifficultyError("difficulty must be easy, medium, or hard")
    return normalized


def _load_word_list(path: Path) -> tuple[str, ...]:
    if not path.is_file():
        raise InvalidWordListError(f"missing word list: {path}")

    words: list[str] = []
    seen: set[str] = set()
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        word = raw.strip().lower()
        if not word:
            continue
        if not word.isalpha():
            raise InvalidWordListError(
                f"{path.name}:{line_number}: {raw!r} is not alphabetic"
            )
        if word in seen:
            continue
        seen.add(word)
        words.append(word)

    if not words:
        raise InvalidWordListError(f"{path.name} has no words")
    return tuple(words)
