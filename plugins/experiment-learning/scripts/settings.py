"""Per-user state lives outside the installed plugin; importing does not write files."""
from pathlib import Path
import json
import math
import os
import uuid

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
default_base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local" / "share")))
DATA_HOME = Path(os.environ.get("EXPERIMENT_LEARNING_HOME", str(default_base / "CodexExperimentLearning"))).expanduser().resolve()
CONFIG_PATH = DATA_HOME / "config.json"
CARDS_PATH = DATA_HOME / "cards.json"
CODEX_STATE_HOME = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser().resolve()
DEFAULT_CONFIG = PLUGIN_ROOT / "assets" / "config.example.json"
DEFAULT_CARDS = PLUGIN_ROOT / "assets" / "cards.example.json"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def load_config():
    config = read_json(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        config.update(read_json(CONFIG_PATH))
    if config["thread_id"] is not None:
        config["thread_id"] = str(uuid.UUID(config["thread_id"]))
    for key in ("stable_seconds", "expected_min_seconds", "unknown_seconds", "poll_seconds", "queue_timeout_seconds", "reply_timeout_seconds"):
        if not isinstance(config[key], (int, float)) or not math.isfinite(config[key]) or config[key] <= 0:
            raise ValueError(f"{key} must be a positive finite number")
    for key in ("quiet_start", "quiet_end"):
        if not isinstance(config[key], int) or not 0 <= config[key] <= 23:
            raise ValueError(f"{key} must be an hour between 0 and 23")
    if not isinstance(config["utc_offset_hours"], (int, float)) or not -12 <= config["utc_offset_hours"] <= 14:
        raise ValueError("utc_offset_hours must be between -12 and 14")
    return config


def load_cards():
    cards = read_json(CARDS_PATH if CARDS_PATH.exists() else DEFAULT_CARDS)
    return validate_cards(cards)


def validate_cards(cards):
    required = {"id", "topic", "prerequisites", "minutes", "explanation", "example", "question", "answer"}
    if not isinstance(cards, list):
        raise ValueError("cards.json must contain a list")
    seen = set()
    for card in cards:
        if not isinstance(card, dict) or not required <= card.keys():
            raise ValueError("A learning card is missing required fields")
        if not isinstance(card["id"], str) or not card["id"] or card["id"] in seen:
            raise ValueError("Card ids must be unique, non-empty strings")
        if any(not isinstance(card[key], str) or not card[key].strip() for key in ("topic", "explanation", "example", "question", "answer")):
            raise ValueError("Card text fields must be non-empty strings")
        if (not isinstance(card["prerequisites"], list)
                or any(not isinstance(value, str) or not value for value in card["prerequisites"])
                or isinstance(card["minutes"], bool) or not isinstance(card["minutes"], (int, float))
                or not math.isfinite(card["minutes"]) or card["minutes"] <= 0):
            raise ValueError("Invalid card prerequisites or duration")
        seen.add(card["id"])
    graph = {card["id"]: card["prerequisites"] for card in cards}
    if any(prerequisite not in seen for card in cards for prerequisite in card["prerequisites"]):
        raise ValueError("A prerequisite references a missing card id")
    visiting, completed = set(), set()
    def visit(card_id):
        if card_id in visiting:
            raise ValueError("Card prerequisites contain a cycle")
        if card_id in completed:
            return
        visiting.add(card_id)
        for prerequisite in graph[card_id]:
            visit(prerequisite)
        visiting.remove(card_id)
        completed.add(card_id)
    for card_id in graph:
        visit(card_id)
    return cards


def initialize():
    DATA_HOME.mkdir(parents=True, exist_ok=True)
    for target, source in ((CONFIG_PATH, DEFAULT_CONFIG), (CARDS_PATH, DEFAULT_CARDS)):
        if not target.exists():
            try:
                with target.open("x", encoding="utf-8") as stream:
                    stream.write(source.read_text(encoding="utf-8"))
            except FileExistsError:
                pass


def save_config(config):
    initialize()
    temporary = CONFIG_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(config, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    temporary.replace(CONFIG_PATH)


def paths():
    return {"home": str(DATA_HOME), "config": str(CONFIG_PATH), "cards": str(CARDS_PATH), "runtime": str(DATA_HOME / "runtime")}


if __name__ == "__main__":
    print(json.dumps(paths(), ensure_ascii=False))
