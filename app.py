"""
app.py
======
The Flask web application: it connects the web page to the game logic.

Run it with:   python app.py
Then open:     http://127.0.0.1:5000

How the pieces fit together
---------------------------
  Browser (script.js)  --JSON-->  Flask routes (this file)
                                     |-- game_logic.py   rules + current match
                                     |-- stats_manager.py  lifetime stats in data/stats.json

  * The CURRENT MATCH is kept in Flask's `session` (a signed cookie).
  * The LIFETIME STATISTICS are kept in a JSON file on this computer.
"""

import os
import secrets

from flask import Flask, jsonify, render_template, request, session
from werkzeug.exceptions import HTTPException

from game_logic import (
    ALLOWED_BEST_OF,
    CHOICE_DETAILS,
    CHOICES,
    InvalidChoiceError,
    InvalidMatchLengthError,
    MatchFinishedError,
    MatchState,
)
from stats_manager import StatsManager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_STATS_FILE = os.path.join(BASE_DIR, "data", "stats.json")

# Friendly messages shown instead of technical error pages.
HTTP_ERROR_MESSAGES = {
    400: "That request was not understood.",
    404: "That page does not exist.",
    405: "That action is not allowed here.",
    413: "That request was too large.",
}
GENERIC_ERROR_MESSAGE = "Something went wrong on the server. Please try again."
SAVE_WARNING = (
    "Your statistics could not be saved to disk this time. "
    "The game still works, but the latest numbers may be lost if the server stops."
)


def create_app(stats_file=DEFAULT_STATS_FILE):
    """Build and return the Flask app.

    Using a function (an "application factory") lets the unit tests create an
    app that writes to a temporary statistics file instead of your real one.
    """
    app = Flask(__name__)

    # The secret key signs the session cookie so it cannot be edited by the player.
    # A new random key is made each time the server starts, which simply means a
    # running match is forgotten when the server restarts (saved statistics stay).
    app.config["SECRET_KEY"] = os.environ.get("RPS_SECRET_KEY") or secrets.token_hex(32)
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["MAX_CONTENT_LENGTH"] = 4 * 1024  # our requests are tiny; refuse big ones

    stats = StatsManager(stats_file)

    # ----- helper functions -------------------------------------------------

    def load_match():
        """Get the current match from the session, or start a new one."""
        saved = session.get("match")
        if saved is None:
            return MatchState()
        try:
            return MatchState.from_dict(saved)
        except (ValueError, TypeError):
            # The saved data looks wrong: start fresh instead of crashing.
            return MatchState()

    def save_match(match):
        session["match"] = match.to_dict()

    def build_state(match):
        """Everything the web page needs to draw itself."""
        return {
            "match": match.to_view(),
            "history": match.recent_history(),
            "stats": stats.get_stats(),
        }

    def ok_response(match, warning=None):
        payload = {"ok": True, "state": build_state(match)}
        if warning:
            payload["warning"] = warning
        return jsonify(payload)

    def error_response(message, status, match=None):
        payload = {"ok": False, "error": message}
        if match is not None:
            payload["state"] = build_state(match)  # lets the page re-sync itself
        return jsonify(payload), status

    def read_json_body():
        """Return the JSON body as a dictionary (an empty one if it is missing/invalid)."""
        data = request.get_json(silent=True)
        return data if isinstance(data, dict) else {}

    def friendly_error(message, status):
        """Same friendly message for the API (JSON) and for normal pages (HTML)."""
        if request.path.startswith("/api/"):
            return jsonify({"ok": False, "error": message}), status
        page = (
            "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            "<title>RPS Arena</title></head>"
            "<body style='font-family:sans-serif;background:#0b1020;color:#eef1ff;padding:2rem'>"
            f"<h1>RPS Arena</h1><p>{message}</p>"
            "<p><a style='color:#38bdf8' href='/'>Back to the game</a></p></body></html>"
        )
        return page, status

    # ----- page route -------------------------------------------------------

    @app.get("/")
    def index():
        choices = [{"name": name, **CHOICE_DETAILS[name]} for name in CHOICES]
        return render_template("index.html", choices=choices, best_of_options=ALLOWED_BEST_OF)

    # ----- API routes (the page talks to these using fetch) -----------------

    @app.get("/api/state")
    def get_state():
        return ok_response(load_match())

    @app.post("/api/play")
    def play():
        match = load_match()
        data = read_json_body()
        try:
            # play_round() validates the choice, makes the computer's random
            # choice, scores the round and updates the history.
            round_info = match.play_round(data.get("choice"))
        except InvalidChoiceError as error:
            return error_response(str(error), 400, match)
        except MatchFinishedError as error:
            return error_response(str(error), 409, match)

        saved = stats.record_round(round_info["result"], match.streak)
        save_match(match)
        return ok_response(match, warning=None if saved else SAVE_WARNING)

    @app.post("/api/new-match")
    def new_match():
        match = load_match()
        data = read_json_body()
        try:
            fresh_match = match.start_new_match(data.get("best_of"))
        except InvalidMatchLengthError as error:
            return error_response(str(error), 400, match)

        save_match(fresh_match)  # only the match changes; saved statistics are untouched
        return ok_response(fresh_match)

    @app.post("/api/reset-stats")
    def reset_stats():
        match = load_match()
        data = read_json_body()
        # The server insists on an explicit confirmation, not just a click.
        if data.get("confirm") is not True:
            return error_response("Please confirm before resetting your statistics.", 400, match)

        saved = stats.reset()
        # Also start a clean match so the page never shows a streak or a history
        # that no longer matches the (now empty) statistics.
        fresh_match = MatchState(best_of=match.best_of)
        save_match(fresh_match)
        return ok_response(fresh_match, warning=None if saved else SAVE_WARNING)

    # ----- error handlers: users never see Python tracebacks ----------------

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        message = HTTP_ERROR_MESSAGES.get(error.code, "Something went wrong with that request.")
        return friendly_error(message, error.code)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        # The full details go to the server console for the developer only.
        app.logger.exception("Unexpected error while handling %s", request.path)
        return friendly_error(GENERIC_ERROR_MESSAGE, 500)

    return app


if __name__ == "__main__":
    application = create_app()
    print("RPS Arena is running at http://127.0.0.1:5000  (press Ctrl+C to stop)")
    # debug=False on purpose: debug mode would show Python tracebacks in the browser.
    application.run(host="127.0.0.1", port=5000, debug=False)
