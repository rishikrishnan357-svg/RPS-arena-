"""
stats_manager.py
================
Saves and loads the player's overall (lifetime) statistics in a JSON file.

Saved fields:  wins, losses, draws, total_rounds, best_streak
(No names, no emails, no personal information is stored.)

Safety features, explained in simple words:
  * A missing, empty or damaged file never crashes the app - we start from zero.
  * The file is written to a temporary file first and then swapped in, so a
    failed write cannot destroy the old statistics file.
  * A lock stops two web requests from changing the numbers at the same moment.
"""

import json
import logging
import os
import tempfile
import threading

logger = logging.getLogger(__name__)

# The starting point for a brand-new player.
DEFAULT_STATS = {
    "wins": 0,
    "losses": 0,
    "draws": 0,
    "total_rounds": 0,
    "best_streak": 0,
}


def _is_valid_count(value):
    """True for whole numbers that are 0 or more (True/False do not count)."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def clean_stats(data):
    """Turn whatever we read from the file into a safe, consistent dictionary.

    * Wrong or missing values become 0.
    * total_rounds is always recalculated as wins + losses + draws,
      so the numbers can never disagree.
    * best_streak cannot be bigger than the number of wins.
    """
    if not isinstance(data, dict):
        return dict(DEFAULT_STATS)

    cleaned = {}
    for key in ("wins", "losses", "draws", "best_streak"):
        value = data.get(key, 0)
        cleaned[key] = value if _is_valid_count(value) else 0

    cleaned["total_rounds"] = cleaned["wins"] + cleaned["losses"] + cleaned["draws"]
    cleaned["best_streak"] = min(cleaned["best_streak"], cleaned["wins"])
    return {key: cleaned[key] for key in DEFAULT_STATS}  # keep a fixed key order


class StatsManager:
    """Keeps the lifetime statistics in memory and in a JSON file."""

    def __init__(self, file_path):
        self.file_path = file_path
        self._lock = threading.Lock()
        self.stats = self.load()

    # ----- loading ----------------------------------------------------------

    def load(self):
        """Read the JSON file. Never raises: on any problem we return zeros."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as stats_file:
                data = json.load(stats_file)
        except FileNotFoundError:
            # First run: there is simply no file yet. This is normal.
            return dict(DEFAULT_STATS)
        except (OSError, ValueError) as error:
            # OSError  -> the file could not be opened/read.
            # ValueError -> empty file or invalid JSON (JSONDecodeError is a ValueError).
            logger.warning("Could not read %s (%s). Starting from zero.",
                           self.file_path, error)
            return dict(DEFAULT_STATS)
        return clean_stats(data)

    # ----- saving -----------------------------------------------------------

    def save(self):
        """Write the statistics to disk. Returns True on success, False on failure.

        Steps: write a temporary file next to the real one, then use
        os.replace() to swap it in. If anything goes wrong, the old file is
        still exactly as it was.
        """
        folder = os.path.dirname(self.file_path) or "."
        temp_path = None
        try:
            os.makedirs(folder, exist_ok=True)
            file_descriptor, temp_path = tempfile.mkstemp(
                dir=folder, prefix="stats_", suffix=".tmp"
            )
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as temp_file:
                json.dump(self.stats, temp_file, indent=2)
            os.replace(temp_path, self.file_path)
            return True
        except OSError as error:
            logger.warning("Could not save statistics to %s (%s).",
                           self.file_path, error)
            # Tidy up the temporary file if it was created.
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            return False

    # ----- using the statistics --------------------------------------------

    def get_stats(self):
        """Return a COPY of the statistics so callers cannot change ours by mistake."""
        with self._lock:
            return dict(self.stats)

    def record_round(self, result, current_streak):
        """Add one finished round to the statistics and save.

        result          'win', 'lose' or 'draw' (from the player's point of view)
        current_streak  the player's consecutive wins AFTER this round

        Returns True if the file was saved, False if saving failed
        (the numbers in memory are still updated).
        """
        with self._lock:
            if result == "win":
                self.stats["wins"] += 1
            elif result == "lose":
                self.stats["losses"] += 1
            elif result == "draw":
                self.stats["draws"] += 1
            else:
                raise ValueError(f"Unknown round result: {result!r}")

            self.stats["total_rounds"] += 1
            # The best streak only ever goes up.
            self.stats["best_streak"] = max(self.stats["best_streak"], current_streak)
            return self.save()

    def reset(self):
        """Set every statistic back to zero and save. Returns True if saved."""
        with self._lock:
            self.stats = dict(DEFAULT_STATS)
            return self.save()
