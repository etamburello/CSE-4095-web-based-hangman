"""API tests. Every game action goes through the Flask test client."""

import tempfile
import unittest
from pathlib import Path

from word_manager import DIFFICULTIES, WordManager

from server import create_app


PLAYING_FIELDS = {
    "game_id",
    "pattern",
    "guessed_letters",
    "incorrect_letters",
    "remaining_guesses",
    "status",
}
FINISHED_FIELDS = PLAYING_FIELDS | {"word"}


def assert_public_fields(test, payload, secret=None):
    """A playing game exposes only the public fields, never an answer."""
    if payload.get("status") == "playing":
        test.assertEqual(set(payload), PLAYING_FIELDS)
    else:
        test.assertEqual(set(payload), FINISHED_FIELDS)
    if secret is None or payload.get("status") != "playing":
        return
    test.assertNotEqual(payload["pattern"].replace(" ", ""), secret)
    for value in payload.values():
        if isinstance(value, str):
            test.assertNotEqual(value, secret)
        elif isinstance(value, list):
            test.assertNotIn(secret, value)


class FixedWordApiTests(unittest.TestCase):
    def setUp(self):
        self._directory = tempfile.TemporaryDirectory()
        root = Path(self._directory.name)
        (root / "easy.txt").write_text("cat\n", encoding="utf-8")
        (root / "medium.txt").write_text("river\n", encoding="utf-8")
        (root / "hard.txt").write_text("mountain\n", encoding="utf-8")
        self.words = {"easy": "cat", "medium": "river", "hard": "mountain"}
        self.client = create_app(WordManager(root)).test_client()

    def tearDown(self):
        self._directory.cleanup()

    def test_create_starts_each_difficulty_without_the_word(self):
        for difficulty, word in self.words.items():
            with self.subTest(difficulty=difficulty):
                response = self.client.post(
                    "/api/games",
                    json={"difficulty": difficulty},
                )
                self.assertEqual(response.status_code, 201)
                payload = response.get_json()
                self.assertEqual(payload["status"], "playing")
                self.assertEqual(payload["remaining_guesses"], 6)
                self.assertEqual(payload["guessed_letters"], [])
                self.assertEqual(payload["incorrect_letters"], [])
                self.assertEqual(payload["pattern"], " ".join("_" * len(word)))
                self.assertTrue(payload["game_id"])
                self._assert_word_hidden(payload, word)

    def test_correct_and_incorrect_guesses(self):
        game_id = self._create("easy")

        correct = self.client.post(
            f"/api/games/{game_id}/guess",
            json={"letter": "C"},
        )
        self.assertEqual(correct.status_code, 200)
        correct_body = correct.get_json()
        self.assertEqual(correct_body["pattern"], "c _ _")
        self.assertEqual(correct_body["guessed_letters"], ["c"])
        self.assertEqual(correct_body["incorrect_letters"], [])
        self.assertEqual(correct_body["remaining_guesses"], 6)
        self.assertEqual(correct_body["status"], "playing")
        self._assert_word_hidden(correct_body, "cat")

        incorrect = self.client.post(
            f"/api/games/{game_id}/guess",
            json={"letter": "z"},
        )
        self.assertEqual(incorrect.status_code, 200)
        incorrect_body = incorrect.get_json()
        self.assertEqual(incorrect_body["pattern"], "c _ _")
        self.assertEqual(incorrect_body["guessed_letters"], ["c", "z"])
        self.assertEqual(incorrect_body["incorrect_letters"], ["z"])
        self.assertEqual(incorrect_body["remaining_guesses"], 5)
        self.assertEqual(incorrect_body["status"], "playing")
        self._assert_word_hidden(incorrect_body, "cat")

        fetched = self.client.get(f"/api/games/{game_id}")
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.get_json(), incorrect_body)

    def test_repeated_and_invalid_guesses_do_not_change_state(self):
        game_id = self._create("easy")
        self.client.post(f"/api/games/{game_id}/guess", json={"letter": "c"})
        before = self.client.get(f"/api/games/{game_id}").get_json()

        for letter in ("c", "C", "", "cc", "1", "c!"):
            with self.subTest(letter=letter):
                response = self.client.post(
                    f"/api/games/{game_id}/guess",
                    json={"letter": letter},
                )
                self.assertEqual(response.status_code, 400)
                self.assertIsInstance(response.get_json()["error"], str)
                self.assertEqual(
                    self.client.get(f"/api/games/{game_id}").get_json(),
                    before,
                )

    def test_win_reveals_the_word_and_then_rejects_guesses(self):
        game_id = self._create("easy")
        for letter in ("c", "a"):
            response = self.client.post(
                f"/api/games/{game_id}/guess",
                json={"letter": letter},
            )
            self.assertEqual(response.status_code, 200)
            self._assert_word_hidden(response.get_json(), "cat")

        won = self.client.post(
            f"/api/games/{game_id}/guess",
            json={"letter": "t"},
        )
        self.assertEqual(won.status_code, 200)
        won_body = won.get_json()
        self.assertEqual(won_body["status"], "won")
        self.assertEqual(won_body["pattern"], "c a t")
        self.assertEqual(won_body["word"], "cat")
        self.assertEqual(won_body["remaining_guesses"], 6)

        rejected = self.client.post(
            f"/api/games/{game_id}/guess",
            json={"letter": "z"},
        )
        self.assertEqual(rejected.status_code, 400)
        self.assertEqual(self.client.get(f"/api/games/{game_id}").get_json(), won_body)

    def test_loss_reveals_the_word(self):
        game_id = self._create("easy")
        body = None
        for letter in ("b", "d", "f", "g", "h", "j"):
            response = self.client.post(
                f"/api/games/{game_id}/guess",
                json={"letter": letter},
            )
            self.assertEqual(response.status_code, 200)
            body = response.get_json()
            if body["status"] == "playing":
                self._assert_word_hidden(body, "cat")

        self.assertEqual(body["status"], "lost")
        self.assertEqual(body["remaining_guesses"], 0)
        self.assertEqual(body["word"], "cat")
        self.assertEqual(body["pattern"], "_ _ _")

    def test_a_new_game_is_independent_of_a_finished_one(self):
        finished = self._create("medium")
        for letter in "river":
            self.client.post(
                f"/api/games/{finished}/guess",
                json={"letter": letter},
            )
        finished_state = self.client.get(f"/api/games/{finished}").get_json()
        self.assertEqual(finished_state["status"], "won")

        started = self.client.post("/api/games", json={"difficulty": " hard "})
        self.assertEqual(started.status_code, 201)
        new_state = started.get_json()
        self.assertNotEqual(new_state["game_id"], finished)
        self.assertEqual(new_state["status"], "playing")
        self.assertEqual(new_state["guessed_letters"], [])
        self.assertEqual(new_state["pattern"], "_ _ _ _ _ _ _ _")
        self._assert_word_hidden(new_state, "mountain")
        self.assertEqual(
            self.client.get(f"/api/games/{finished}").get_json(),
            finished_state,
        )

    def test_invalid_requests(self):
        created = self._create("easy")

        cases = [
            ("post", "/api/games", {"json": {}}, 400),
            ("post", "/api/games", {"json": {"difficulty": "expert"}}, 400),
            ("post", "/api/games", {"json": {"difficulty": 1}}, 400),
            ("post", "/api/games", {"data": "", "content_type": "application/json"}, 400),
            (
                "post",
                "/api/games",
                {"data": "{not json", "content_type": "application/json"},
                400,
            ),
            (
                "post",
                "/api/games",
                {"data": "[]", "content_type": "application/json"},
                400,
            ),
            ("get", "/api/games/missing", {}, 404),
            ("post", "/api/games/missing/guess", {"json": {"letter": "e"}}, 404),
            ("post", f"/api/games/{created}/guess", {"json": {}}, 400),
            (
                "post",
                f"/api/games/{created}/guess",
                {"json": {"letter": 1}},
                400,
            ),
            (
                "post",
                f"/api/games/{created}/guess",
                {"data": "not-json", "content_type": "text/plain"},
                400,
            ),
        ]
        for method, path, kwargs, status in cases:
            with self.subTest(method=method, path=path, status=status):
                response = getattr(self.client, method)(path, **kwargs)
                self.assertEqual(response.status_code, status)
                self.assertIsInstance(response.get_json()["error"], str)
                self.assertNotIn("word", response.get_json())

    def _create(self, difficulty: str) -> str:
        response = self.client.post("/api/games", json={"difficulty": difficulty})
        self.assertEqual(response.status_code, 201)
        return response.get_json()["game_id"]

    def _assert_word_hidden(self, payload: dict, secret: str) -> None:
        assert_public_fields(self, payload, secret)


class ShippedWordListApiTests(unittest.TestCase):
    def test_each_difficulty_can_be_played_until_the_end(self):
        manager = WordManager()
        client = create_app(manager).test_client()

        for difficulty in DIFFICULTIES:
            with self.subTest(difficulty=difficulty):
                created = client.post("/api/games", json={"difficulty": difficulty})
                self.assertEqual(created.status_code, 201)
                state = created.get_json()
                self.assertEqual(state["status"], "playing")
                assert_public_fields(self, state)
                game_id = state["game_id"]
                slots = state["pattern"].split(" ")

                final = None
                for letter in "abcdefghijklmnopqrstuvwxyz":
                    response = client.post(
                        f"/api/games/{game_id}/guess",
                        json={"letter": letter},
                    )
                    self.assertIn(response.status_code, (200, 400))
                    if response.status_code == 400:
                        self.assertNotIn("word", response.get_json())
                        continue
                    final = response.get_json()
                    if final["status"] == "playing":
                        assert_public_fields(self, final)
                        continue
                    break

                self.assertIsNotNone(final)
                self.assertIn(final["status"], ("won", "lost"))
                assert_public_fields(self, final)
                self.assertIn(final["word"], manager.words(difficulty))
                self.assertEqual(len(slots), len(final["word"]))
                self.assertEqual(len(slots), len(final["pattern"].split(" ")))


if __name__ == "__main__":
    unittest.main()
