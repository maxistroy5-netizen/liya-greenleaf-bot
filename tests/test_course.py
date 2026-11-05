import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
import unittest

from lia_course import CourseResult, CourseStore, load_catalog, render, revision_token


class CatalogTests(unittest.TestCase):
    def test_both_catalogs_preserve_all_22_source_answers(self):
        source = json.loads((Path(__file__).parents[1] / "course/source_ru.json").read_text())
        for code in ("ru", "uz"):
            data = load_catalog(code)
            self.assertEqual([x["id"] for x in data["lessons"]], list("12345678"))
            self.assertEqual([len(x["quiz"]) for x in data["lessons"]], [3, 3, 3, 3, 3, 3, 1, 3])
            for a, b in zip(source["lessons"], data["lessons"], strict=True):
                self.assertEqual([(q["id"], q["correct"]) for q in a["quiz"]],
                                 [(q["id"], q["correct"]) for q in b["quiz"]])

    def test_mutated_numbers_options_and_keys_are_rejected(self):
        ru = load_catalog("ru")
        uz = load_catalog("uz")
        mutations = [
            lambda data: data["lessons"][2].update(body=data["lessons"][2]["body"].replace("88 $", "89 $", 1)),
            lambda data: data["lessons"][3]["quiz"][0].update(correct="B"),
            lambda data: data["lessons"][4]["quiz"][1]["options"].update(A="12%", B="10%"),
            lambda data: data["lessons"][2].update(body=data["lessons"][2]["body"].replace("88 $ × 70 ₽", "70 ₽ × 88 $")),
        ]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "ru.json").write_text(json.dumps(ru))
            for mutate in mutations:
                changed = copy.deepcopy(uz)
                mutate(changed)
                (root / "uz.json").write_text(json.dumps(changed))
                with self.assertRaises(ValueError):
                    load_catalog("uz", root)

    def test_untranslated_locale_is_not_silently_replaced_with_russian(self):
        with self.assertRaises(ValueError):
            load_catalog("fr")


class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "state.sqlite3"
        self.store = CourseStore(self.path)

    def quiz(self):
        state = self.store.get(10)
        return self.store.act(10, "quiz", expected_revision=state["revision"])

    def test_every_lesson_and_answer_in_both_languages(self):
        for user_id, code in enumerate(("ru", "uz"), 10):
            catalog = load_catalog(code)
            self.store.act(user_id, "open", lesson=1)
            for item in catalog["lessons"]:
                state = self.store.get(user_id)
                self.assertEqual(state["lesson"], int(item["id"]))
                result = self.store.act(user_id, "quiz", expected_revision=state["revision"])
                for i, question in enumerate(item["quiz"]):
                    state = result.state
                    body, buttons = render(catalog, result)
                    self.assertIn(question["prompt"], body)
                    self.assertEqual(state["question"], i)
                    self.assertTrue(all(len(payload.encode()) <= 64 for _, payload in buttons))
                    wrong = next(value for value in "ABC" if value != question["correct"])
                    result = self.store.act(user_id, "answer", expected_revision=state["revision"], answer=wrong)
                    self.assertEqual(result.feedback, "wrong")
                    self.assertEqual(result.state["question"], i)
                    self.assertIn(question["hint"], render(catalog, result)[0])
                    result = self.store.act(user_id, "answer", expected_revision=result.state["revision"], answer=question["correct"])
                self.assertEqual(result.state["phase"], "done")
                self.assertIn(int(item["id"]), result.state["completed"])
                if int(item["id"]) < 8:
                    self.store.act(user_id, "next", expected_revision=result.state["revision"])
            self.assertEqual(self.store.get(user_id)["completed"], list(range(1, 9)))

    def test_restart_and_language_switch_keep_same_question(self):
        result = self.quiz()
        result = self.store.act(10, "answer", expected_revision=result.state["revision"], answer="B")
        restored = CourseStore(self.path)
        state = restored.get(10)
        self.assertEqual(state["question"], 1)
        for code in ("ru", "uz"):
            body, _ = render(load_catalog(code), CourseResult(state))
            self.assertIn(load_catalog(code)["lessons"][0]["quiz"][1]["prompt"], body)

    def test_stale_button_cannot_answer_next_question(self):
        state = self.quiz().state
        result = self.store.act(10, "answer", expected_revision=state["revision"], answer="B")
        duplicate = self.store.act(10, "answer", expected_revision=state["revision"], answer="B")
        self.assertEqual(duplicate.feedback, "stale")
        self.assertEqual(duplicate.state, result.state)

    def test_concurrent_duplicate_only_advances_once(self):
        state = self.quiz().state
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.store.act(10, "answer", expected_revision=state["revision"], answer="B"), range(2)))
        self.assertEqual(sum(item.feedback == "stale" for item in results), 1)
        self.assertEqual(self.store.get(10)["question"], 1)

    def test_users_and_course_versions_are_isolated(self):
        self.quiz()
        self.assertEqual(self.store.get(20)["phase"], "lesson")
        changed = load_catalog("ru")
        changed["version"] = "future-version"
        new_store = CourseStore(self.path, changed)
        self.assertEqual(new_store.get(10)["phase"], "lesson")
        with self.assertRaises(ValueError):
            new_store.parse_revision(revision_token(self.store.version, 1))

    def test_cannot_skip_test_or_advance_with_invalid_answer(self):
        result = self.store.act(10, "next", expected_revision=0)
        self.assertEqual(result.feedback, "stale")
        self.assertEqual(result.state["lesson"], 1)
        state = self.quiz().state
        for answer in ("D", "", None, "l1q1"):
            result = self.store.act(10, "answer", expected_revision=state["revision"], answer=answer)
            self.assertEqual(result.feedback, "stale")
            self.assertEqual(result.state, state)
