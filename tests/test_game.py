"""Unit tests for the Hangman game engine."""

import ast
import unittest
from pathlib import Path

from game import HangmanGame, InvalidGuessError


class HangmanGameTests(unittest.TestCase):
    def test_initial_state_hides_the_word(self):
        game = HangmanGame("eagle")
        state = game.to_state()

        self.assertEqual(state["pattern"], "_ _ _ _ _")
        self.assertEqual(state["guessed_letters"], [])
        self.assertEqual(state["incorrect_letters"], [])
        self.assertEqual(state["remaining_guesses"], 6)
        self.assertEqual(state["status"], "playing")
        self.assertNotIn("word", state)

    def test_correct_guess_reveals_every_match_without_costing_a_life(self):
        game = HangmanGame("eagle")

        state = game.guess("e")

        self.assertEqual(state["pattern"], "e _ _ _ e")
        self.assertEqual(state["guessed_letters"], ["e"])
        self.assertEqual(state["incorrect_letters"], [])
        self.assertEqual(state["remaining_guesses"], 6)
        self.assertEqual(state["status"], "playing")
        self.assertNotIn("word", state)

    def test_guesses_are_case_insensitive(self):
        game = HangmanGame("Eagle")

        state = game.guess("E")

        self.assertEqual(state["pattern"], "e _ _ _ e")
        self.assertEqual(state["guessed_letters"], ["e"])
        self.assertEqual(state["status"], "playing")

    def test_incorrect_guess_costs_one_life(self):
        game = HangmanGame("eagle")

        state = game.guess("z")

        self.assertEqual(state["pattern"], "_ _ _ _ _")
        self.assertEqual(state["guessed_letters"], ["z"])
        self.assertEqual(state["incorrect_letters"], ["z"])
        self.assertEqual(state["remaining_guesses"], 5)
        self.assertEqual(state["status"], "playing")
        self.assertNotIn("word", state)

    def test_duplicate_guess_is_rejected_and_state_is_unchanged(self):
        game = HangmanGame("eagle")
        game.guess("e")
        before = game.to_state()

        with self.assertRaises(InvalidGuessError):
            game.guess("E")

        self.assertEqual(game.to_state(), before)

    def test_invalid_guesses_are_rejected(self):
        game = HangmanGame("eagle")
        before = game.to_state()

        for guess in ("", " ", "ee", "1", "e!", None, 5):
            with self.subTest(guess=guess):
                with self.assertRaises(InvalidGuessError):
                    game.guess(guess)
                self.assertEqual(game.to_state(), before)

    def test_repeated_letters_in_the_word_are_revealed_together(self):
        game = HangmanGame("book")

        state = game.guess("o")

        self.assertEqual(state["pattern"], "_ o o _")
        self.assertEqual(state["remaining_guesses"], 6)

    def test_win_reveals_the_word(self):
        game = HangmanGame("a")

        state = game.guess("a")

        self.assertEqual(state["status"], "won")
        self.assertEqual(state["pattern"], "a")
        self.assertEqual(state["word"], "a")
        self.assertEqual(state["remaining_guesses"], 6)

    def test_win_after_misses_still_reveals_the_normalized_word(self):
        game = HangmanGame("Be")
        game.guess("x")
        state = game.guess("b")
        state = game.guess("e")

        self.assertEqual(state["status"], "won")
        self.assertEqual(state["pattern"], "b e")
        self.assertEqual(state["word"], "be")
        self.assertEqual(state["incorrect_letters"], ["x"])
        self.assertEqual(state["remaining_guesses"], 5)

    def test_loss_reveals_the_word_when_lives_run_out(self):
        game = HangmanGame("a", max_incorrect_guesses=2)
        game.guess("b")

        state = game.guess("c")

        self.assertEqual(state["status"], "lost")
        self.assertEqual(state["pattern"], "_")
        self.assertEqual(state["remaining_guesses"], 0)
        self.assertEqual(state["incorrect_letters"], ["b", "c"])
        self.assertEqual(state["word"], "a")

    def test_default_allowance_is_six_incorrect_guesses(self):
        game = HangmanGame("a")
        for letter in "bcdefg":
            state = game.guess(letter)

        self.assertEqual(state["status"], "lost")
        self.assertEqual(state["remaining_guesses"], 0)
        self.assertEqual(state["word"], "a")

    def test_guess_after_win_is_rejected(self):
        game = HangmanGame("a")
        game.guess("a")
        before = game.to_state()

        with self.assertRaises(InvalidGuessError):
            game.guess("b")

        self.assertEqual(game.to_state(), before)
        self.assertEqual(before["status"], "won")

    def test_guess_after_loss_is_rejected(self):
        game = HangmanGame("a", max_incorrect_guesses=1)
        game.guess("z")
        before = game.to_state()

        with self.assertRaises(InvalidGuessError):
            game.guess("a")

        self.assertEqual(game.to_state(), before)
        self.assertEqual(before["status"], "lost")
        self.assertEqual(before["word"], "a")

    def test_state_lists_are_copies(self):
        game = HangmanGame("eagle")
        state = game.to_state()
        state["guessed_letters"].append("z")
        state["incorrect_letters"].append("z")

        self.assertEqual(game.to_state()["guessed_letters"], [])
        self.assertEqual(game.to_state()["incorrect_letters"], [])

    def test_playing_state_never_contains_the_hidden_word(self):
        game = HangmanGame("eagle")
        game.guess("e")
        game.guess("z")
        state = game.to_state()

        self.assertEqual(state["status"], "playing")
        self.assertNotIn("word", state)
        for value in state.values():
            self.assertNotEqual(value, "eagle")
            if isinstance(value, str):
                self.assertNotIn("eagle", value)

    def test_constructor_rejects_an_unusable_word(self):
        for word in ("", "   ", "hi there", "abc123", "can't"):
            with self.subTest(word=word):
                with self.assertRaises(ValueError):
                    HangmanGame(word)

    def test_constructor_rejects_a_bad_guess_allowance(self):
        with self.assertRaises(ValueError):
            HangmanGame("eagle", max_incorrect_guesses=0)
        with self.assertRaises(TypeError):
            HangmanGame("eagle", max_incorrect_guesses=True)

    def test_engine_module_does_not_depend_on_flask(self):
        source = Path(__file__).resolve().parents[1].joinpath("game.py").read_text()
        tree = ast.parse(source)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])

        self.assertNotIn("flask", imported)


if __name__ == "__main__":
    unittest.main()
