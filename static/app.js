const parts = ["part-1", "part-2", "part-3", "part-4", "part-5", "part-6"];
const notice = document.getElementById("notice");
const reveal = document.getElementById("reveal");
const pattern = document.getElementById("pattern");
const remaining = document.getElementById("remaining");
const guessed = document.getElementById("guessed");
const incorrect = document.getElementById("incorrect");
const keys = Array.from(document.querySelectorAll(".key"));

let gameId = null;
let playing = false;
let sending = false;

document.getElementById("setup").addEventListener("submit", (event) => {
  event.preventDefault();
  beginGame();
});

keys.forEach((button) => {
  button.addEventListener("click", () => {
    submitGuess(button.dataset.letter);
  });
});

document.addEventListener("keydown", (event) => {
  if (event.metaKey || event.ctrlKey || event.altKey) {
    return;
  }
  const tag = event.target && event.target.tagName;
  if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA") {
    return;
  }
  if (event.key.length !== 1 || !/[a-z]/i.test(event.key)) {
    return;
  }
  event.preventDefault();
  submitGuess(event.key.toLowerCase());
});

async function beginGame() {
  const difficulty = document.getElementById("difficulty").value;
  notice.textContent = "Starting…";
  try {
    const response = await fetch("/api/games", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ difficulty }),
    });
    const payload = await response.json();
    if (!response.ok) {
      notice.textContent = payload.error || "Could not start.";
      return;
    }
    gameId = payload.game_id;
    showState(payload);
  } catch (error) {
    notice.textContent = "Could not reach the server.";
  }
}

async function submitGuess(character) {
  if (!gameId || !playing || sending) {
    return;
  }
  const button = keys.find((item) => item.dataset.letter === character);
  if (button && button.disabled) {
    return;
  }
  sending = true;
  try {
    const response = await fetch(`/api/games/${gameId}/guess`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ letter: character }),
    });
    const payload = await response.json();
    if (!response.ok) {
      notice.textContent = payload.error || "Guess rejected.";
      return;
    }
    showState(payload);
  } catch (error) {
    notice.textContent = "Could not reach the server.";
  } finally {
    sending = false;
  }
}

function showState(state) {
  playing = state.status === "playing";
  pattern.textContent = state.pattern;
  remaining.textContent = String(state.remaining_guesses);
  guessed.textContent = state.guessed_letters.length
    ? state.guessed_letters.join(" ")
    : "—";
  incorrect.textContent = state.incorrect_letters.length
    ? state.incorrect_letters.join(" ")
    : "—";

  const used = new Set(state.guessed_letters);
  const misses = new Set(state.incorrect_letters);
  keys.forEach((button) => {
    const character = button.dataset.letter;
    const already = used.has(character);
    button.disabled = !playing || already;
    button.classList.toggle("hit", already && !misses.has(character));
    button.classList.toggle("miss", misses.has(character));
  });

  const missCount = state.incorrect_letters.length;
  parts.forEach((id, index) => {
    document.getElementById(id).classList.toggle("drawn", index < missCount);
  });

  reveal.hidden = !state.word;
  reveal.textContent = state.word ? state.word : "";
  notice.classList.remove("won", "lost");
  if (state.status === "won") {
    notice.classList.add("won");
    notice.textContent = state.word ? `You won. It was ${state.word}.` : "You won.";
  } else if (state.status === "lost") {
    notice.classList.add("lost");
    notice.textContent = state.word ? `You lost. It was ${state.word}.` : "You lost.";
  } else {
    notice.textContent = "Guess a character.";
  }
}
