# TODO — Web-Based Hangman

This file is the implementation roadmap for the web Hangman assignment.

The required work is the Hangman server and the browser client. A terminal client, automated bots, bot evaluation, scoring, and a leaderboard are out of scope. `Specification.md` and `cursor_transcript.md` are reference material for the game rules, the REST contract, and a Render deployment. Where this plan and the larger specification disagree, this plan wins.

## Implementation Rules

- Implement one phase at a time.
- Complete and test every item in the current phase before starting the next phase.
- Keep the game engine independent of Flask and the browser.
- The server is authoritative. The browser displays server state and submits guesses. It does not decide whether a guess is correct.
- Never send the hidden word while `status` is `playing`.
- Add tests as each phase is implemented. Phase 5 checks the assignment’s full verification list before deployment.
- Do not implement the out-of-scope features listed above.

## Decisions locked in for this assignment

The specification leaves a few choices open. Use these so the API stays stable:

| Decision | Choice |
|---|---|
| Framework | Flask |
| Incorrect guesses allowed | 6 |
| Duplicate guesses | Reject. Do not change game state. |
| Guesses after the game ends | Reject |
| Invalid guesses | Reject empty, multi-character, and non-letter input |
| Letter case | Normalize words and guesses to lowercase |
| Word pattern | Spaces between characters, as in `"_ e _ _ e"` |
| Answer field | `word`, included only when `status` is `won` or `lost` |
| Game storage | In memory, one process. A restart clears active games. |
| Error body | JSON object with an `error` string |

Create-game response:

```json
{
    "game_id": "abc123",
    "pattern": "_ _ _ _ _",
    "remaining_guesses": 6,
    "status": "playing"
}
```

Guess and get-state responses use the same shape. `game_id` is optional on get and guess. Include `guessed_letters` and `incorrect_letters` on every state response, including create. Include `word` only after the game ends.

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

HTTP status codes: `201` on create, `200` on get and a successful guess, `400` for invalid input, `404` for an unknown game id.

---

## Phase 1 — Core Game Engine

The engine can be tested with a word passed in directly. Word files and Flask are not part of this phase.

### Tasks

- [x] Create `game.py`.
- [x] Implement a `HangmanGame` class that stores the hidden word internally.
- [x] Track guessed letters and incorrect letters separately.
- [x] Allow six incorrect guesses by default.
- [x] Accept one alphabetic letter per guess and normalize it to lowercase.
- [x] Reject empty, multi-character, non-letter, and duplicate guesses.
- [x] Reject any guess after the game is won or lost.
- [x] Build the spaced word pattern.
- [x] Decrement remaining guesses only for a new incorrect letter.
- [x] Detect a win when every letter is revealed.
- [x] Detect a loss when remaining guesses reach 0 and letters are still hidden.
- [x] Use status values `playing`, `won`, and `lost`.
- [x] Return a client-safe state dictionary.
- [x] Include `word` in that dictionary only after a win or loss.
- [x] Add unit tests for the rules above.

### Completion Criteria

The game engine can be tested without a web server, a browser, or the word files.

Correct guesses, incorrect guesses, invalid guesses, duplicate guesses, wins, losses, and answer disclosure are covered by unit tests.

---

## Phase 2 — Word Lists and Difficulty

### Tasks

- [ ] Add `words/easy.txt`, `words/medium.txt`, and `words/hard.txt`.
- [ ] Create a word-loading module that is independent of Flask and the browser.
- [ ] Load each difficulty list.
- [ ] Lowercase words, skip blanks, drop duplicates, and reject non-alphabetic entries.
- [ ] Select a random word by difficulty: `easy`, `medium`, or `hard`.
- [ ] Reject an unknown difficulty with a clear error.
- [ ] Add tests for loading, validation, random selection, and invalid difficulty.

### Completion Criteria

The program can request a random word for each difficulty.

Invalid difficulty values are rejected cleanly.

The game engine still does not import Flask.

---

## Phase 3 — Flask Server and REST API

### Tasks

- [ ] Create `server.py` and `requirements.txt` with Flask.
- [ ] Create the Flask application and an in-memory store of active games.
- [ ] Generate a unique id for each game.
- [ ] Keep a separate `HangmanGame` for each id.
- [ ] Implement `POST /api/games` with a JSON body `{"difficulty": "medium"}`.
- [ ] Select the hidden word on the server from the requested difficulty.
- [ ] Implement `GET /api/games/{game_id}`.
- [ ] Implement `POST /api/games/{game_id}/guess` with a JSON body `{"letter": "e"}`.
- [ ] Validate difficulty and guess input.
- [ ] Return JSON for success and error responses.
- [ ] Return `201`, `200`, `400`, and `404` as defined above.
- [ ] Handle an unknown game id, a missing body, and malformed JSON.
- [ ] Omit the hidden word from every response while `status` is `playing`.
- [ ] Add API tests that play through the HTTP interface only.

### Completion Criteria

A complete game can be played with `curl` or another HTTP client.

The browser is not required for this phase.

Tests cover all three difficulties, correct and incorrect guesses, repeated and invalid guesses, win and loss, a new game after a finished one, invalid requests, and the rule that the hidden word stays on the server during play.

---

## Phase 4 — Browser Client

### Tasks

- [ ] Create `static/index.html`, `static/style.css`, and `static/app.js`.
- [ ] Serve the page from Flask at `/`.
- [ ] Add an Easy / Medium / Hard selector.
- [ ] Add a New Game button that starts a game through `POST /api/games`.
- [ ] Display the current word pattern.
- [ ] Display previously guessed letters and incorrect letters.
- [ ] Display the number of remaining incorrect guesses.
- [ ] Add an on-screen A–Z keyboard and physical keyboard input.
- [ ] Disable letters that have already been guessed.
- [ ] Submit every guess with `fetch()` to `POST /api/games/{game_id}/guess`.
- [ ] Draw the hangman figure and update it as incorrect guesses accumulate.
- [ ] Show a win or loss message, and show the word only after the server reveals it.
- [ ] Let the player start another game without reloading the page.
- [ ] Keep the layout usable on a desktop window and a narrow phone-sized window.
- [ ] Add tests that the served page contains the controls and does not embed a word list or a hidden word.

### Completion Criteria

A player can finish a game in the browser against the local server, then start another game on the same page.

No hidden word and no independent game engine live in the browser JavaScript. The page renders the state returned by the API.

---

## Phase 5 — Assignment Verification

Confirm every testing requirement before deployment. Fill any gap with an automated test. Use the browser for the drawing, keyboard, and new-game flow.

### Tasks

- [ ] Start games at easy, medium, and hard.
- [ ] Record a correct guess and an incorrect guess.
- [ ] Reject a repeated guess and an invalid guess without changing state.
- [ ] Win a game and confirm the word is revealed only then.
- [ ] Lose a game and confirm the word is revealed only then.
- [ ] Start a new game after a completed game and confirm the new id and pattern.
- [ ] Reject invalid API requests: bad difficulty, missing letter, non-JSON body, unknown game id.
- [ ] Confirm active-game responses have no `word` field and no other answer field.
- [ ] In the browser, confirm the pattern, guessed letters, remaining guesses, drawing, and win/loss message update after each guess.
- [ ] In the browser, confirm keyboard and button guesses both reach the API.
- [ ] In the browser, confirm a second game starts without a reload.

### Completion Criteria

The engine, the API, and the browser flow are all checked against the assignment’s testing list.

Automated tests pass with:

```bash
python3 -m unittest discover -s tests -t . -v
```

---

## Phase 6 — Packaging

### Tasks

- [ ] Document installation, how to start the server, and how to open the browser client.
- [ ] Document the three REST endpoints with example requests and responses.
- [ ] Document the guess rules and the point at which the word is revealed.
- [ ] Pin runtime dependencies in `requirements.txt`, including a production server.
- [ ] Run the app from the documented commands on a fresh local start.

### Completion Criteria

A new user can install dependencies, start the server, and play in a browser using only the documentation.

---

## Phase 7 — Cloud Deployment

Deploy to Render, or another host that runs a Python web process. GitHub Pages is not sufficient because the game needs the Flask process.

### Tasks

- [ ] Add a production start command that binds one worker to `$PORT`:

    ```bash
    gunicorn --bind 0.0.0.0:$PORT --workers 1 server:app
    ```

- [ ] Keep debug mode off in production. One worker shares the in-memory games.
- [ ] Add the host configuration, such as `render.yaml`, and document the build and start commands.
- [ ] Deploy from the project repository.
- [ ] Open the public HTTPS URL and confirm the Hangman page loads.
- [ ] Create a game, make guesses, finish the game, and start another game in the deployed browser UI.
- [ ] Confirm `POST /api/games`, `GET /api/games/{game_id}`, and `POST /api/games/{game_id}/guess` respond on the public URL.
- [ ] Confirm a visitor can play without installing Python or running a local server.

### Completion Criteria

The public HTTPS site serves the web interface and the REST API, and a complete game can be played in the browser.

On Render’s free tier, the service may sleep after idle time. The first request after sleep can take up to a minute. Games in memory are cleared when the service restarts.

---

## Out of Scope

Do not implement these, even though `Specification.md` and the later phases of the original TODO describe them:

- Terminal client
- Automated bots and dictionary strategies
- Evaluation sessions, scoring, and a leaderboard
- Logging and replay tools
- Accounts, a database, and multiplayer

## Recommended Order

1. Core game engine
2. Word lists and difficulty
3. Flask REST API
4. Browser client
5. Assignment verification
6. Packaging
7. Cloud deployment

The project should remain runnable after every completed phase.
