"""Flask server for the Hangman REST API.

The server stores games in memory and delegates every rule to
HangmanGame. It does not reveal the hidden word while a game is playing.

Start it locally with:

    python3 server.py
"""

from __future__ import annotations

import uuid

from flask import Flask, jsonify, request, send_from_directory

from game import HangmanGame, InvalidGuessError
from word_manager import InvalidDifficultyError, WordManager


def create_app(word_manager: WordManager | None = None) -> Flask:
    """Build a Flask app with its own in-memory game store."""
    app = Flask(__name__)
    manager = word_manager if word_manager is not None else WordManager()
    games: dict[str, HangmanGame] = {}

    @app.post("/api/games")
    def create_game():
        body, error = _json_object()
        if error is not None:
            return error
        difficulty = body.get("difficulty")
        if not isinstance(difficulty, str):
            return _error("difficulty must be easy, medium, or hard", 400)
        try:
            word = manager.random_word(difficulty)
        except InvalidDifficultyError as exc:
            return _error(str(exc), 400)
        game_id = _new_game_id(games)
        games[game_id] = HangmanGame(word)
        return jsonify(_public_state(game_id, games[game_id])), 201

    @app.get("/api/games/<game_id>")
    def get_game(game_id: str):
        game = games.get(game_id)
        if game is None:
            return _error("game not found", 404)
        return jsonify(_public_state(game_id, game))

    @app.post("/api/games/<game_id>/guess")
    def guess_letter(game_id: str):
        game = games.get(game_id)
        if game is None:
            return _error("game not found", 404)
        body, error = _json_object()
        if error is not None:
            return error
        if "letter" not in body:
            return _error("letter is required", 400)
        letter = body["letter"]
        if not isinstance(letter, str):
            return _error("guess must be a single letter", 400)
        try:
            game.guess(letter)
        except InvalidGuessError as exc:
            return _error(str(exc), 400)
        return jsonify(_public_state(game_id, game))

    @app.get("/")
    def home():
        return send_from_directory(app.static_folder, "index.html")

    return app


def _json_object():
    if not request.is_json:
        return None, _error("request body must be a JSON object", 400)
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return None, _error("request body must be a JSON object", 400)
    return body, None


def _public_state(game_id: str, game: HangmanGame) -> dict:
    return {"game_id": game_id, **game.to_state()}


def _new_game_id(games: dict[str, HangmanGame]) -> str:
    game_id = uuid.uuid4().hex
    while game_id in games:
        game_id = uuid.uuid4().hex
    return game_id


def _error(message: str, status: int):
    return jsonify(error=message), status


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
