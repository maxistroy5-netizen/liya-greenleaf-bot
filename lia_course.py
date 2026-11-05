"""Deterministic text lessons and assessments. No model calls or Telegram imports."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parent / "course"
AVAILABLE_LANGUAGES = ("ru", "uz")


def protected_values(value):
    # Preserve exact original number formatting, currency and PV; never convert.
    return tuple(re.findall(r"\d+(?:[ .,]\d+)*|PV|[%$₽×=]", value))


def revision_token(version, revision):
    return hashlib.sha256(version.encode()).hexdigest()[:8] + "." + str(revision)


def load_catalog(code, root=ROOT):
    if code not in AVAILABLE_LANGUAGES:
        raise ValueError("Course translation not available")
    data = json.loads((root / f"{code}.json").read_text(encoding="utf-8"))
    if data.get("language") != code:
        raise ValueError("Catalog language mismatch")
    source = json.loads((root / "ru.json").read_text(encoding="utf-8"))
    if data.get("version") != source["version"] or set(data["ui"]) != set(source["ui"]):
        raise ValueError("Course version or UI keys mismatch")
    if len(data["lessons"]) != 8:
        raise ValueError("Expected exactly eight source lessons")
    for original, translated in zip(source["lessons"], data["lessons"], strict=True):
        if original["id"] != translated["id"] or not translated["title"].strip():
            raise ValueError("Lesson identity mismatch")
        if protected_values(original["body"]) != protected_values(translated["body"]):
            raise ValueError("Lesson numbers, currency or PV changed")
        if len(original["quiz"]) != len(translated["quiz"]):
            raise ValueError("Question count changed")
        for a, b in zip(original["quiz"], translated["quiz"], strict=True):
            if a["id"] != b["id"] or a["correct"] != b["correct"] or b["correct"] not in {"A", "B", "C"}:
                raise ValueError("Answer key or question identity changed")
            if set(b["options"]) != set("ABC"):
                raise ValueError("Option identities changed")
            for value_a, value_b in [(a["prompt"], b["prompt"]), (a["hint"], b["hint"])] + [(a["options"][key], b["options"][key]) for key in "ABC"]:
                if not value_b.strip() or protected_values(value_a) != protected_values(value_b):
                    raise ValueError("Question facts changed or text missing")
    return data


@dataclass(frozen=True)
class CourseResult:
    state: dict
    feedback: str = ""


class CourseStore:
    def __init__(self, path, catalog=None):
        self.path = Path(path)
        self.catalog = catalog or load_catalog("ru")
        self.version = self.catalog["version"]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS course_progress ("
                       "user_id INTEGER NOT NULL, version TEXT NOT NULL, state TEXT NOT NULL, "
                       "PRIMARY KEY(user_id, version))")

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def _read(self, db, user_id):
        row = db.execute("SELECT state FROM course_progress WHERE user_id=? AND version=?",
                         (int(user_id), self.version)).fetchone()
        return json.loads(row[0]) if row else {"lesson": 1, "question": 0, "phase": "lesson", "completed": [], "revision": 0}

    def get(self, user_id):
        with self.connect() as db:
            return self._read(db, user_id)

    def parse_revision(self, token):
        prefix, value = token.split(".", 1)
        if prefix != revision_token(self.version, 0).split(".")[0]:
            raise ValueError("Course version changed")
        return int(value)

    def act(self, user_id, action, *, expected_revision=None, lesson=None, answer=None):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            state = self._read(db, user_id)
            if action not in {"open", "resume", "quiz", "answer", "next"}:
                return CourseResult(state, "stale")
            if action not in {"open", "resume"} and expected_revision != state["revision"]:
                return CourseResult(state, "stale")
            feedback = ""
            if action == "open":
                if not isinstance(lesson, int) or not 1 <= lesson <= 8:
                    return CourseResult(state, "stale")
                if lesson != state["lesson"] or state["phase"] == "done":
                    state.update(lesson=lesson, question=0, phase="lesson")
            elif action == "quiz":
                if state["phase"] != "lesson":
                    return CourseResult(state, "stale")
                state.update(phase="quiz", question=0)
            elif action == "answer":
                if state["phase"] != "quiz" or answer not in {"A", "B", "C"}:
                    return CourseResult(state, "stale")
                questions = self.catalog["lessons"][state["lesson"] - 1]["quiz"]
                if answer != questions[state["question"]]["correct"]:
                    feedback = "wrong"
                elif state["question"] + 1 < len(questions):
                    state["question"] += 1
                else:
                    state["phase"] = "done"
                    state["completed"] = sorted(set(state["completed"] + [state["lesson"]]))
            elif action == "next":
                if state["phase"] != "done" or state["lesson"] == 8:
                    return CourseResult(state, "stale")
                state.update(lesson=state["lesson"] + 1, question=0, phase="lesson")
            state["revision"] += 1
            db.execute("INSERT INTO course_progress VALUES (?, ?, ?) "
                       "ON CONFLICT(user_id,version) DO UPDATE SET state=excluded.state",
                       (int(user_id), self.version, json.dumps(state)))
            return CourseResult(state, feedback)


def render(data, result):
    """Return text and (label, stable payload) tuples, without disclosing keys."""
    state, ui = result.state, data["ui"]
    item = data["lessons"][state["lesson"] - 1]
    heading = f'{ui["lesson"]} {item["id"]} | {item["title"]}'
    revision = revision_token(data["version"], state["revision"])
    if state["phase"] == "quiz":
        question = item["quiz"][state["question"]]
        body = question["prompt"] + "\n\n" + "\n".join(f'{key} — {question["options"][key]}' for key in "ABC")
        if result.feedback == "wrong":
            body = question["hint"] + "\n\n" + body
        buttons = [(key, f"course:answer:{revision}:{key}") for key in "ABC"]
    elif state["phase"] == "done":
        body = ui["done"]
        buttons = [(ui["next"], f"course:next:{revision}")] if state["lesson"] < 8 else []
    else:
        body = item["body"] + "\n\n" + ui["review"]
        buttons = [(ui["check"], f"course:quiz:{revision}")]
    if result.feedback == "stale":
        body = ui["stale"] + "\n\n" + body
    buttons.extend([(ui["title"], "course:menu"), (ui["home"], "nav:home")])
    return heading + "\n\n" + body, buttons
