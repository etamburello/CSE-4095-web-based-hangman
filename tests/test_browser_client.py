"""Tests for the page served to the browser."""

import string
import unittest

from word_manager import DIFFICULTIES, WordManager

from server import create_app


class BrowserClientTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_homepage_has_the_game_controls(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        response.close()

        self.assertIn('id="difficulty"', html)
        self.assertIn('value="easy"', html)
        self.assertIn('value="medium"', html)
        self.assertIn('value="hard"', html)
        self.assertIn(">Easy<", html)
        self.assertIn(">Medium<", html)
        self.assertIn(">Hard<", html)
        self.assertIn('id="new-game-button"', html)
        self.assertIn('id="pattern"', html)
        self.assertIn('id="remaining"', html)
        self.assertIn('id="guessed"', html)
        self.assertIn('id="incorrect"', html)
        self.assertIn('id="notice"', html)
        self.assertIn("<svg", html)
        for part in range(1, 7):
            self.assertIn(f'id="part-{part}"', html)
        for letter in string.ascii_lowercase:
            self.assertIn(f'data-letter="{letter}"', html)
        self.assertIn("/static/app.js", html)
        self.assertIn("/static/style.css", html)

    def test_assets_are_served(self):
        script = self.client.get("/static/app.js")
        style = self.client.get("/static/style.css")
        self.assertEqual(script.status_code, 200)
        self.assertEqual(style.status_code, 200)
        self.assertIn("fetch(", script.get_data(as_text=True))
        self.assertIn("@media", style.get_data(as_text=True))
        script.close()
        style.close()

    def test_script_talks_to_the_api_and_does_not_embed_words(self):
        page = self.client.get("/")
        script = self.client.get("/static/app.js")
        style = self.client.get("/static/style.css")
        html = page.get_data(as_text=True)
        source = script.get_data(as_text=True)
        css = style.get_data(as_text=True)
        page.close()
        script.close()
        style.close()

        self.assertIn('fetch("/api/games"', source)
        self.assertIn("/guess", source)
        self.assertIn("state.word", source)
        self.assertIn("state.status", source)
        self.assertNotIn("easy.txt", source)
        self.assertNotIn("medium.txt", source)
        self.assertNotIn("hard.txt", source)
        self.assertNotIn("words/", source + html + css)
        self.assertNotRegex(
            source,
            r"(hidden|secret|candidates)\s*[:=]\s*['\"][a-z]",
        )

        combined = f"{html}\n{source}\n{css}".lower()
        for difficulty in DIFFICULTIES:
            words = WordManager().words(difficulty)
            for start in range(0, len(words) - 8, 8):
                chunk = words[start : start + 8]
                self.assertNotIn(" ".join(chunk), combined)
                self.assertNotIn("\n".join(chunk), combined)
                self.assertNotIn(",".join(chunk), combined)


if __name__ == "__main__":
    unittest.main()
