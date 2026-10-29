"""
game_logic.py
=============
All the rules of Rock Paper Scissors live in this file.

There is NO Flask code here. That is on purpose:
  * the rules can be tested on their own (see tests/),
  * app.py stays small and only deals with web requests.

What is inside:
  * constants      - the allowed choices, the "who beats who" table, etc.
  * functions      - validate_choice, determine_winner, get_computer_choice ...
  * MatchState     - a class that remembers one best-of match
"""

import random

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# The only three moves the game accepts (a tuple cannot be changed by accident).
CHOICES = ("rock", "paper", "scissors")

# A dictionary that answers "what does this move beat?"
#   rock beats scissors, scissors beats paper, paper beats rock.
BEATS = {
    "rock": "scissors",
    "scissors": "paper",
    "paper": "rock",
}

# Text and emoji used by the web page to draw each choice.
# (Hand-gesture emoji are used because they work on older Windows versions too.)
CHOICE_DETAILS = {
    "rock": {"label": "Rock", "emoji": "✊"},
    "paper": {"label": "Paper", "emoji": "✋"},
    "scissors": {"label": "Scissors", "emoji": "✌️"},
}

# The three possible results of one round, always from the PLAYER's point of view.
WIN = "win"
LOSE = "lose"
DRAW = "draw"
RESULTS = (WIN, LOSE, DRAW)

# Match lengths the player may pick.
ALLOWED_BEST_OF = (3, 5, 7)
DEFAULT_BEST_OF = 3

# How many recent rounds we remember and show.
HISTORY_LIMIT = 10


# ---------------------------------------------------------------------------
# Custom errors
# ---------------------------------------------------------------------------
# Own error classes make the code easier to read: app.py can say
# "except InvalidChoiceError" instead of guessing what went wrong.

class InvalidChoiceError(ValueError):
    """The player's choice was not rock, paper or scissors."""


class InvalidMatchLengthError(ValueError):
    """The requested match length was not 3, 5 or 7."""


class MatchFinishedError(Exception):
    """A round was attempted after the match had already been decided."""


# ---------------------------------------------------------------------------
# Small helper functions
# ---------------------------------------------------------------------------

def validate_choice(value):
    """Return the choice if it is exactly 'rock', 'paper' or 'scissors'.

    Anything else (None, numbers, 'lizard', 'ROCK', an empty string ...)
    raises InvalidChoiceError. The server never trusts what the browser sends.
    """
    if not isinstance(value, str) or value not in CHOICES:
        raise InvalidChoiceError("Please choose rock, paper, or scissors.")
    return value


def validate_best_of(value):
    """Return the match length if it is 3, 5 or 7, otherwise raise an error."""
    # bool is a special kind of int in Python (True == 1), so we reject it first.
    is_whole_number = isinstance(value, int) and not isinstance(value, bool)
    if not is_whole_number or value not in ALLOWED_BEST_OF:
        raise InvalidMatchLengthError("Match length must be 3, 5, or 7.")
    return value


def determine_winner(player_choice, computer_choice):
    """Decide one round. Returns 'win', 'lose' or 'draw' for the PLAYER."""
    player_choice = validate_choice(player_choice)
    computer_choice = validate_choice(computer_choice)

    if player_choice == computer_choice:
        return DRAW
    if BEATS[player_choice] == computer_choice:
        return WIN
    return LOSE


def get_computer_choice():
    """Pick the computer's move at random (done on the server, never in the browser)."""
    return random.choice(CHOICES)


def _non_negative_int(value, name):
    """Helper: make sure a stored number is a whole number that is 0 or more."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a whole number that is 0 or more.")
    return value


# ---------------------------------------------------------------------------
# MatchState - remembers everything about the current match
# ---------------------------------------------------------------------------

class MatchState:
    """One best-of-3, best-of-5 or best-of-7 match against the computer.

    The object stores only the raw counts. Things like "is the match over?" or
    "who won?" are CALCULATED from those counts (see the properties below),
    so they can never disagree with the scores.
    """

    def __init__(self, best_of=DEFAULT_BEST_OF, streak=0):
        self.best_of = validate_best_of(best_of)
        self.player_wins = 0
        self.computer_wins = 0
        self.draws = 0
        # Number of wins in a row for the player. A loss or a draw sets it to 0.
        self.streak = _non_negative_int(streak, "streak")
        # Recent rounds, oldest first. Never longer than HISTORY_LIMIT.
        self.history = []

    # ----- values calculated from the counts --------------------------------

    @property
    def wins_needed(self):
        """Wins required to take the match: 2 for best of 3, 3 for 5, 4 for 7."""
        return self.best_of // 2 + 1

    @property
    def rounds_played(self):
        """Every round counts, including draws."""
        return self.player_wins + self.computer_wins + self.draws

    @property
    def winner(self):
        """'player', 'computer', or None while the match is still going."""
        if self.player_wins >= self.wins_needed:
            return "player"
        if self.computer_wins >= self.wins_needed:
            return "computer"
        return None

    @property
    def finished(self):
        return self.winner is not None

    # ----- playing ----------------------------------------------------------

    def play_round(self, player_choice, computer_choice=None):
        """Play one round and return a dictionary describing it.

        Raises InvalidChoiceError   -> nothing is changed.
        Raises MatchFinishedError   -> nothing is changed.

        `computer_choice` exists ONLY so that unit tests can force a move.
        The web app never passes it, so the computer's move is always random.
        """
        # 1. Check the input first, before touching any score.
        player_choice = validate_choice(player_choice)
        if computer_choice is None:
            computer_choice = get_computer_choice()
        else:
            computer_choice = validate_choice(computer_choice)

        # 2. A finished match cannot be scored any further.
        if self.finished:
            raise MatchFinishedError(
                "This match is over. Start a new match to keep playing."
            )

        # 3. Decide the round and update the scores and the streak.
        result = determine_winner(player_choice, computer_choice)
        if result == WIN:
            self.player_wins += 1
            self.streak += 1
        elif result == LOSE:
            self.computer_wins += 1
            self.streak = 0
        else:
            self.draws += 1
            self.streak = 0

        # 4. Remember the round, keeping only the most recent ones.
        round_info = {
            "round": self.rounds_played,
            "player": player_choice,
            "computer": computer_choice,
            "result": result,
        }
        self.history.append(round_info)
        self.history = self.history[-HISTORY_LIMIT:]
        return round_info

    def start_new_match(self, best_of=None):
        """Return a FRESH match (scores and history reset).

        If best_of is None the same length is used again. The player's
        win-streak is carried over, because it counts consecutive wins overall.
        This method never touches the saved statistics file.
        """
        if best_of is None:
            best_of = self.best_of
        return MatchState(best_of=best_of, streak=self.streak)

    # ----- turning the object into plain data -------------------------------

    def recent_history(self):
        """Recent rounds, NEWEST first (this is what the page shows)."""
        return [dict(entry) for entry in reversed(self.history)]

    def to_view(self):
        """Plain dictionary sent to the browser."""
        return {
            "best_of": self.best_of,
            "wins_needed": self.wins_needed,
            "player_wins": self.player_wins,
            "computer_wins": self.computer_wins,
            "draws": self.draws,
            "rounds_played": self.rounds_played,
            "finished": self.finished,
            "winner": self.winner,
            "streak": self.streak,
        }

    def to_dict(self):
        """Plain dictionary stored in the Flask session (a signed cookie)."""
        return {
            "best_of": self.best_of,
            "player_wins": self.player_wins,
            "computer_wins": self.computer_wins,
            "draws": self.draws,
            "streak": self.streak,
            "history": [dict(entry) for entry in self.history],
        }

    @classmethod
    def from_dict(cls, data):
        """Rebuild a MatchState from session data.

        Every value is checked again. If anything looks wrong a ValueError is
        raised and app.py simply starts a fresh match instead of crashing.
        """
        if not isinstance(data, dict):
            raise ValueError("Saved match data must be a dictionary.")

        match = cls(best_of=data.get("best_of"), streak=data.get("streak", 0))
        match.player_wins = _non_negative_int(data.get("player_wins"), "player_wins")
        match.computer_wins = _non_negative_int(data.get("computer_wins"), "computer_wins")
        match.draws = _non_negative_int(data.get("draws"), "draws")

        raw_history = data.get("history", [])
        if not isinstance(raw_history, list):
            raise ValueError("Saved history must be a list.")

        cleaned_history = []
        for entry in raw_history:
            if not isinstance(entry, dict):
                raise ValueError("Each history entry must be a dictionary.")
            result = entry.get("result")
            if result not in RESULTS:
                raise ValueError("History entry has an unknown result.")
            cleaned_history.append({
                "round": _non_negative_int(entry.get("round"), "round"),
                "player": validate_choice(entry.get("player")),
                "computer": validate_choice(entry.get("computer")),
                "result": result,
            })
        match.history = cleaned_history[-HISTORY_LIMIT:]
        return match
