"""Tests for loading words and selecting one by difficulty."""

import ast
import random
import tempfile
import unittest
from pathlib import Path

from game import HangmanGame
from word_manager import (
    DIFFICULTIES,
    InvalidDifficultyError,
    InvalidWordListError,
    WordManager,
)


ROOT = Path(__file__).resolve().parents[1]
WORDS_DIR = ROOT / "words"


class ShippedWordListTests(unittest.TestCase):
    def test_each_difficulty_loads_unique_lowercase_words(self):
        manager = WordManager(WORDS_DIR)

        for difficulty in DIFFICULTIES:
            with self.subTest(difficulty=difficulty):
                words = manager.words(difficulty)
                self.assertGreater(len(words), 0)
                self.assertEqual(len(words), len(set(words)))
                for word in words:
                    self.assertTrue(word.isalpha())
                    self.assertEqual(word, word.lower())

    def test_random_word_comes_from_the_requested_list(self):
        manager = WordManager(WORDS_DIR)
        rng = random.Random(7)

        for difficulty in DIFFICULTIES:
            with self.subTest(difficulty=difficulty):
                word = manager.random_word(difficulty, rng=rng)
                self.assertIn(word, manager.words(difficulty))
                HangmanGame(word)

    def test_difficulty_names_are_case_insensitive(self):
        manager = WordManager(WORDS_DIR)

        self.assertEqual(manager.words(" Easy "), manager.words("easy"))
        self.assertIn(
            manager.random_word("MEDIUM", rng=random.Random(1)),
            manager.words("medium"),
        )

    def test_unknown_difficulty_is_rejected(self):
        manager = WordManager(WORDS_DIR)

        for difficulty in ("", "expert", "easy medium", None, 1):
            with self.subTest(difficulty=difficulty):
                with self.assertRaises(InvalidDifficultyError):
                    manager.words(difficulty)
                with self.assertRaises(InvalidDifficultyError):
                    manager.random_word(difficulty)

    def test_seeded_selection_is_stable(self):
        manager = WordManager(WORDS_DIR)

        first = manager.random_word("hard", rng=random.Random(3))
        second = manager.random_word("hard", rng=random.Random(3))

        self.assertEqual(first, second)


class WordListValidationTests(unittest.TestCase):
    def test_blank_lines_are_skipped_and_duplicates_are_dropped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_lists(
                root,
                easy="Apple\n\n  apple \nANT\n\n",
                medium="river\n",
                hard="mountain\n",
            )
            manager = WordManager(root)

            self.assertEqual(manager.words("easy"), ("apple", "ant"))

    def test_non_alphabetic_entry_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_lists(root, medium="river\nsea-side\n")

            with self.assertRaises(InvalidWordListError):
                WordManager(root)

    def test_empty_list_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_lists(root, hard="\n  \n")

            with self.assertRaises(InvalidWordListError):
                WordManager(root)

    def test_missing_list_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "easy.txt").write_text("apple\n", encoding="utf-8")
            (root / "medium.txt").write_text("river\n", encoding="utf-8")

            with self.assertRaises(InvalidWordListError):
                WordManager(root)


class WordManagerModuleTests(unittest.TestCase):
    def test_module_does_not_depend_on_flask(self):
        source = (ROOT / "word_manager.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])

        self.assertNotIn("flask", imported)
        self.assertNotIn("game", imported)


def _write_lists(root: Path, easy="apple\n", medium="river\n", hard="mountain\n") -> None:
    (root / "easy.txt").write_text(easy, encoding="utf-8")
    (root / "medium.txt").write_text(medium, encoding="utf-8")
    (root / "hard.txt").write_text(hard, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
