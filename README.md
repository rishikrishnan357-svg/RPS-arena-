# RPS Arena — Rock Paper Scissors

A Rock Paper Scissors website built with **Python and Flask**.
You play against the computer in single rounds or in best-of-3 / 5 / 7 matches, with a scoreboard, game history and statistics that are saved between sessions.

*BTCS2101 Programming with Python — Mini Project*

---

## 1. Problem statement

Rock Paper Scissors is simple to describe but is a good small problem for practising real programming skills: the rules must be applied correctly, the computer's choice must be genuinely random, the player's input cannot be trusted, and the results must be remembered consistently. This project builds a complete, working web version of the game that runs on a student laptop with no paid services and no internet connection (after installing Flask).

## 2. Project objectives

- Apply Python **functions, classes and objects, dictionaries and lists, file handling, exception handling and modules** in one working application.
- Keep the **game rules in Python** (server side) instead of trusting the browser.
- **Validate every input** and show friendly messages instead of Python error pages.
- **Store statistics** safely in a JSON file that survives restarts and bad data.
- Build a clean, responsive and accessible user interface using only HTML, CSS and vanilla JavaScript.
- Write automated tests with Python's `unittest` module.

## 3. Features

| # | Feature | What it does |
|---|---------|--------------|
| 1 | **Interactive gameplay** | Click Rock ✊, Paper ✋ or Scissors ✌️. The server picks the computer's move at random, decides the winner and shows *You Win!*, *You Lose!* or *Draw!*. |
| 2 | **Scoreboard** | Your wins, the computer's wins, draws and rounds played in the current match. |
| 3 | **Best-of match mode** | Best of 3, 5 or 7 with progress dots. The match ends when someone reaches the required wins; no more scoring is allowed until you start a new match. |
| 4 | **Game history** | The 10 most recent rounds of the match, newest first. |
| 5 | **Persistent statistics** | Wins, losses, draws, total rounds and best streak saved in `data/stats.json`. A *Reset statistics* button asks for confirmation first. |
| 6 | **Responsive and accessible UI** | Works on laptops and phones; keyboard focus outlines; semantic HTML; screen-reader labels; high-contrast colours; friendly error messages. |

## 4. Technology stack

- **Python 3** (tested with 3.13; any recent Python 3 should work)
- **Flask** — web server and routing (the only dependency)
- **HTML5 / CSS3 / vanilla JavaScript** — the web page
- Python standard library only for everything else: `random`, `json`, `os`, `tempfile`, `threading`, `logging`, `secrets`, `unittest`

No database, no external API, no CDN, no web fonts and no images are used.

## 5. Folder structure

```
rps_arena/
├── app.py               Flask app: routes, session handling, error handlers
├── game_logic.py        Game rules, input validation, MatchState class
├── stats_manager.py     StatsManager class: load/save statistics (JSON file)
├── requirements.txt     Python dependency list (Flask)
├── README.md            This file
├── .gitignore           Files that should not be uploaded to GitHub
├── templates/
│   └── index.html       The web page (Flask/Jinja template)
├── static/
│   ├── style.css        All styling (dark gaming theme, responsive)
│   └── script.js        Browser code: sends clicks to the server, draws results
├── data/
│   └── .gitkeep         Keeps the folder in Git; stats.json is created here
├── tests/
│   ├── test_game_logic.py     Rules, validation, scoring, matches, history
│   ├── test_stats_manager.py  JSON loading/saving, corrupted files, failed writes
│   └── test_app.py            Flask routes, sessions, error handling
└── docs/
    ├── VIVA_GUIDE.md          Explanation of the code for your viva
    └── SUBMISSION_GUIDE.md    Report outline, slide outline, screenshots, checklist
```

## 6. How to install and run (Windows)

**Step 1 — Install Python 3.** Download it from <https://www.python.org/downloads/>. In the installer, tick **“Add python.exe to PATH”**. Check it worked by opening a terminal and typing `python --version`.

**Step 2 — Open the project folder.** In VS Code use *File → Open Folder…* and choose `rps_arena`, then open the built-in terminal with *Terminal → New Terminal*. (Or open Command Prompt / PowerShell and `cd` into the folder.)

**Step 3 — Create a virtual environment** (a private box of Python packages for this project):

```
python -m venv venv
```

**Step 4 — Activate it:**

```
venv\Scripts\activate
```

You should now see `(venv)` at the start of the line.
*PowerShell says “running scripts is disabled”?* Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and activate again, or use Command Prompt instead.

**Step 5 — Install the dependency:**

```
pip install -r requirements.txt
```

**Step 6 — Start the game:**

```
python app.py
```

**Step 7 — Open the website.** Flask prints the address. Open <http://127.0.0.1:5000> in your browser.

**Step 8 — Stop the server.** Click in the terminal and press **Ctrl + C**.

To run it again later, you only need Steps 2, 4 and 6.

### Where are the statistics saved? How do I reset them?

- Lifetime statistics are stored in **`data/stats.json`**, created automatically after the first round. It contains only five numbers (wins, losses, draws, total rounds, best streak).
- To reset them: press **Reset statistics** on the website and confirm, **or** stop the server and delete `data/stats.json`.

## 7. Game rules

- Rock beats Scissors.
- Scissors beats Paper.
- Paper beats Rock.
- The same choice on both sides is a **draw**.

**Matches:** *Best of N* means the first side to win `N // 2 + 1` rounds wins the match (2 for best of 3, 3 for best of 5, 4 for best of 7). Draws are played again; they are counted as rounds but do not count towards winning. Changing the match length (or pressing **New Match**) starts a fresh match; if a match is in progress you are asked to confirm first.

**Streaks:** The streak counts your consecutive round wins. A loss or a draw sets it back to 0. It carries over from one match to the next, and the **best streak** is saved in your statistics.

## 8. The important Python modules

### `game_logic.py` — the rules (no Flask inside)

| Name | Purpose |
|------|---------|
| `validate_choice(value)` | Accepts only the exact strings `rock`, `paper`, `scissors`; otherwise raises `InvalidChoiceError`. |
| `determine_winner(player, computer)` | Returns `"win"`, `"lose"` or `"draw"` for the player, using the `BEATS` dictionary. |
| `get_computer_choice()` | Picks the computer's move with `random.choice`. |
| `validate_best_of(value)` | Accepts only 3, 5 or 7. |
| `class MatchState` | One match: scores, streak and recent history. Methods: `play_round()`, `start_new_match()`, `to_dict()`, `from_dict()`. Properties such as `finished` and `winner` are *calculated* from the scores so they can never disagree with them. |

### `stats_manager.py` — saved statistics

| Name | Purpose |
|------|---------|
| `class StatsManager` | Loads the JSON file, records every round, resets, saves. |
| `load()` | Handles a missing, empty or corrupted file with `try`/`except` and falls back to zeros. |
| `clean_stats()` | Repairs odd values; makes `total_rounds = wins + losses + draws`. |
| `save()` | Writes to a temporary file and then swaps it in with `os.replace`, so a failed write cannot destroy the old file. |

### `app.py` — the web layer

| Route | Purpose |
|-------|---------|
| `GET /` | Shows the page. |
| `GET /api/state` | Returns the current match, history and saved statistics as JSON. |
| `POST /api/play` | Plays a round: validates the choice, the server picks the computer's move, updates scores and statistics. |
| `POST /api/new-match` | Starts a new match (optionally with length 3, 5 or 7). Saved statistics are untouched. |
| `POST /api/reset-stats` | Resets statistics; the server requires `{"confirm": true}`. |

`create_app()` builds the Flask app (this makes it easy to test with a temporary statistics file). Error handlers turn every problem into a short, friendly message and never show a traceback.

## 9. Testing

### Automated tests

From the project folder (with the virtual environment active):

```
python -m unittest discover -s tests -v
```

The tests cover: all three rules and draws, rejection of invalid choices, score updates, best-of completion, blocking rounds after a match ends, new match vs saved statistics, history limit and order, missing/empty/corrupted JSON, failed file writes, the Flask routes, and that internal error details are never shown to the user.

> Some lines such as *“Could not read … Starting from zero”* are printed during the tests. That is expected: those tests deliberately create broken files to prove the app copes.

### Manual testing checklist

Tick each item while the server is running.

- [ ] **Start:** `python app.py` starts without errors and the page opens at `http://127.0.0.1:5000`.
- [ ] **Fresh start:** with no `data/stats.json`, the page loads with all numbers at 0 and “No rounds yet”.
- [ ] **Play rounds:** click Rock, Paper and Scissors several times. Each click shows both choices and a result.
- [ ] **Randomness:** the computer's choices vary; they are not always the same.
- [ ] **Scoreboard:** wins + computer wins + draws = rounds, after every click.
- [ ] **History:** newest round on top; never more than 10 rows; the rows agree with the scoreboard.
- [ ] **Best of 3:** play until someone has 2 wins. The match-over banner appears and the three choice buttons are disabled.
- [ ] **No scoring after the end:** the buttons stay disabled; the numbers no longer change.
- [ ] **Other lengths:** pick Best of 5 and Best of 7; the progress dots change (3 and 4 dots).
- [ ] **New Match mid-game:** play one round, press New Match: a confirmation appears. Cancel keeps the match; confirm resets the match scores but not the overall statistics.
- [ ] **Reload:** press F5 in the middle of a match. The match, history and statistics are still shown.
- [ ] **Restart:** stop the server (Ctrl + C), start it again. Overall statistics are still there (the unfinished match is gone — this is expected).
- [ ] **Best streak:** win 2–3 rounds in a row; “Best streak” updates; a loss or draw resets “Current streak” but not the best streak.
- [ ] **Reset statistics:** press Reset statistics; Cancel changes nothing; confirming sets everything to 0.
- [ ] **Corrupted file:** stop the server, replace `data/stats.json` with the text `hello`, start again. The app starts with zeros and no error page.
- [ ] **Keyboard:** use Tab and Enter/Space only. Focus outlines are visible and every button works.
- [ ] **Mobile layout:** press F12 and click the phone/tablet icon (device toolbar) to simulate a small screen. The layout stacks into one column and nothing is cut off. (The server only listens on this laptop, so you cannot open it from a real phone unless you change the host in `app.py`.)
- [ ] **Bad address:** open `http://127.0.0.1:5000/nothing`. A friendly message appears, not a Python error page.

### Troubleshooting common beginner errors

| Problem | Fix |
|---------|-----|
| `'python' is not recognized` | Python is not on PATH. Reinstall it and tick “Add python.exe to PATH”, or try `py` instead of `python`. |
| `No module named flask` | The virtual environment is not active, or step 5 was skipped. Run `venv\Scripts\activate`, then `pip install -r requirements.txt`. |
| PowerShell “running scripts is disabled” | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, or use Command Prompt. |
| `Address already in use` / port 5000 busy | Another program (or an old copy of this one) is using the port. Close it, or change `port=5000` to `port=5001` at the bottom of `app.py` and open `http://127.0.0.1:5001`. |
| `No module named game_logic` when running tests | Run the command from the project folder (the one containing `app.py`), not from inside `tests/`. |
| Page loads but buttons do nothing | Press **Ctrl + F5** to refresh the cached script. Make sure the terminal shows the server is running. |
| Old match disappears after restarting | Normal: the current match lives in a session cookie that is invalidated when the server restarts. Saved statistics are not affected. |
| Statistics not saving | Check the terminal for a “Could not save statistics” warning. Make sure the `data` folder exists and is not read-only. |

## 10. Known limitations

- **Single-user demo design.** The *current match* is stored per browser in Flask's session cookie, but the *saved statistics* are one shared file for the whole server. If two people use the same running server, their results are added together.
- **The match is forgotten when the server restarts**, because a new random secret key is generated at start-up (this is safer than hard-coding one). Setting an `RPS_SECRET_KEY` environment variable would keep the session valid across restarts.
- The session cookie is **signed, not encrypted**: the player cannot change it, but they could read it in their browser tools. It contains only game scores.
- Uses Flask's built-in **development server**, which is fine for a local demonstration but not for real hosting. There is no login, so there is no protection against someone else on the same computer.
- Only the last 10 rounds of the current match are kept in the history.
- The page needs JavaScript; the game does not work with JavaScript switched off.
- Emoji are drawn by your operating system, so they look slightly different on Windows, Android and Apple devices.

## 11. Acknowledgements and references

**Libraries and tools used**

- [Flask](https://flask.palletsprojects.com/) (BSD-3-Clause licence) — web framework (installed with `pip`).
- Python standard library — <https://docs.python.org/3/> (`random`, `json`, `os`, `tempfile`, `threading`, `unittest`).
- Browser features documented by MDN Web Docs — <https://developer.mozilla.org/> (`fetch`, `<dialog>`, CSS Grid).
- Colour contrast checked against WCAG 2.1 guidance — <https://www.w3.org/WAI/WCAG21/quickref/>.

**Assets:** no images, icons, fonts or code from other websites are used. The game symbols are standard Unicode emoji (✊ ✋ ✌️ 🎉 😢 🤝 🏆 💻) displayed with each device's own emoji font. The layout and colours were written for this project.

**Add here:** your lecture notes, textbook, tutorials or any other source you actually used.

### Declaration of AI assistance

> *Adapt this paragraph so it is true for you before you submit.*
>
> “This project was developed with the assistance of an AI model (Claude, by Anthropic). The AI generated the initial structure and code for the application, the automated tests and the documentation, based on my project requirements. I then **[describe what you personally did — for example: installed and ran the project, tested it manually using the checklist, read and understood every module, changed X, added Y, fixed Z]**. I am able to explain how every part of the code works, and I take responsibility for the submitted work.”

Your institution's rules decide how much AI help is allowed and how it must be declared. Check your course guidelines, and make sure the declaration describes what actually happened.
