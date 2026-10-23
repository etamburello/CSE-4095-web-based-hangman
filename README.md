# Hangman

A browser Hangman game. The Flask server chooses the word and applies every rule. The page shows the state returned by the server and submits guesses. It does not keep the hidden word while a game is in progress.

## Requirements

Python 3.10 or newer.

## Install

From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate the environment with `.venv\Scripts\activate`.

`requirements.txt` pins Flask and Gunicorn. Use the Flask development server below for local play. Gunicorn is the production server.

## Start the server

```bash
python3 server.py
```

The server listens on http://127.0.0.1:5000. Open that address in a browser.

## Play

1. Choose Easy, Medium, or Hard.
2. Press New Game.
3. Guess a letter by clicking it or by typing it.
4. Press New Game again to start another game without reloading the page.

## Rules

- Each guess is one letter. Uppercase and lowercase are the same letter.
- A correct letter is filled in everywhere it occurs and does not cost a guess.
- A new wrong letter costs one guess. Six wrong guesses lose the game.
- An empty guess, a guess of more than one character, a non-letter, or a letter already guessed is rejected. The game does not change.
- A guess sent after the game is won or lost is rejected.
- The pattern puts a space between characters, as in `_ e _ _ e`.
- The server decides the result of every guess.

## When the word is revealed

Responses leave the word out while `status` is `playing`. After a win or a loss, `status` is `won` or `lost` and the response includes `word`.

Games are stored in memory. Stopping the server clears them.

## REST API

Send and receive JSON. A failed request has this shape:

```json
{"error": "game not found"}
```

`POST /api/games` returns `201`. A successful get or guess returns `200`. Invalid input returns `400`. An unknown game id returns `404`.

### Create a game

```bash
curl -s -X POST http://127.0.0.1:5000/api/games \
  -H 'Content-Type: application/json' \
  -d '{"difficulty":"medium"}'
```

```json
{
  "game_id": "abc123",
  "pattern": "_ _ _ _ _",
  "guessed_letters": [],
  "incorrect_letters": [],
  "remaining_guesses": 6,
  "status": "playing"
}
```

`difficulty` is `easy`, `medium`, or `hard`.

### Read the current state

```bash
curl -s http://127.0.0.1:5000/api/games/abc123
```

The body uses the same fields as a guess response. `word` is present only when the game is over.

### Submit a guess

```bash
curl -s -X POST http://127.0.0.1:5000/api/games/abc123/guess \
  -H 'Content-Type: application/json' \
  -d '{"letter":"e"}'
```

```json
{
  "game_id": "abc123",
  "pattern": "_ e _ _ e",
  "guessed_letters": ["e"],
  "incorrect_letters": [],
  "remaining_guesses": 6,
  "status": "playing"
}
```

A finished game adds the answer:

```json
{
  "game_id": "abc123",
  "pattern": "e a g l e",
  "guessed_letters": ["e", "a", "g", "l"],
  "incorrect_letters": [],
  "remaining_guesses": 6,
  "status": "won",
  "word": "eagle"
}
```
