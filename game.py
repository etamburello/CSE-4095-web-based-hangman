"""Hangman game engine.

The engine owns the hidden word and the rules. It does not depend on
Flask, HTTP, or a user interface.
"""

from __future__ import annotations


class InvalidGuessError(ValueError):
    """A guess could not be applied, so the game state was left unchanged."""


class HangmanGame:
    """One Hangman game. The hidden word stays inside the object."""

    def __init__(self, word: str, max_incorrect_guesses: int = 6) -> None:
        if not isinstance(word, str):
            raise TypeError("word must be a string")
        normalized = word.strip().lower()
        if not normalized.isalpha():
            raise ValueError("word must contain only letters")
        if (
            isinstance(max_incorrect_guesses, bool)
            or not isinstance(max_incorrect_guesses, int)
        ):
            raise TypeError("max_incorrect_guesses must be an integer")
        if max_incorrect_guesses < 1:
            raise ValueError("max_incorrect_guesses must be at least 1")

        self._word = normalized
        self._max_incorrect = max_incorrect_guesses
        self._guessed: list[str] = []
        self._incorrect: list[str] = []

    def guess(self, letter: str) -> dict:
        """Apply one letter and return the client-safe state.

        Raises InvalidGuessError without changing state when the guess
        is empty, not a single letter, a duplicate, or made after the
        game has already ended.
        """
        if self.status != "playing":
            raise InvalidGuessError("the game is already over")

        normalized = _normalize_guess(letter)
        if normalized in self._guessed:
            raise InvalidGuessError(f"'{normalized}' was already guessed")

        self._guessed.append(normalized)
        if normalized not in self._word:
            self._incorrect.append(normalized)
        return self.to_state()

    @property
    def status(self) -> str:
        if set(self._word) <= set(self._guessed):
            return "won"
        if len(self._incorrect) >= self._max_incorrect:
            return "lost"
        return "playing"

    @property
    def remaining_guesses(self) -> int:
        return self._max_incorrect - len(self._incorrect)

    @property
    def pattern(self) -> str:
        return " ".join(
            character if character in self._guessed else "_"
            for character in self._word
        )

    def to_state(self) -> dict:
        """Return the state a client is allowed to see.

        ``word`` is included only after a win or a loss.
        """
        state = {
            "pattern": self.pattern,
            "guessed_letters": list(self._guessed),
            "incorrect_letters": list(self._incorrect),
            "remaining_guesses": self.remaining_guesses,
            "status": self.status,
        }
        if self.status != "playing":
            state["word"] = self._word
        return state


def _normalize_guess(letter: str) -> str:
    if not isinstance(letter, str):
        raise InvalidGuessError("guess must be a single letter")
    normalized = letter.strip().lower()
    if len(normalized) != 1 or not normalized.isalpha():
        raise InvalidGuessError("guess must be a single letter")
    return normalized
