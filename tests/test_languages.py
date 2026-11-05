import tempfile
import unittest
from pathlib import Path

from lia_languages import (LANGUAGES, LanguageStore, language_choices,
                           language_instruction, menu_choices,
                           parse_language_choice, reset_navigation)


class LanguageTests(unittest.TestCase):
    def test_all_nine_languages_have_round_trip_choices(self):
        self.assertEqual(set(LANGUAGES), {"ru", "uz", "tg", "ky", "tr", "az", "en", "fr", "de"})
        for label, payload in language_choices():
            self.assertTrue(label)
            self.assertIn(parse_language_choice(payload), LANGUAGES)
            self.assertLessEqual(len(payload.encode()), 64)

    def test_preferences_survive_reopening_and_users_are_isolated(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "preferences.sqlite3"
            store = LanguageStore(path)
            self.assertIsNone(store.get(10))
            store.set(10, "uz")
            store.set(20, "tg")
            store = LanguageStore(path)
            self.assertEqual(store.get(10), "uz")
            self.assertEqual(store.get(20), "tg")
            store.set(10, "de")
            self.assertEqual(store.get(10), "de")
            self.assertEqual(store.get(20), "tg")

    def test_invalid_choices_never_persist(self):
        for payload in (None, "uz", "nav:ask", "lang:xx", "lang:ru:extra"):
            with self.assertRaises(ValueError):
                parse_language_choice(payload)
        with tempfile.TemporaryDirectory() as folder:
            store = LanguageStore(Path(folder) / "preferences.sqlite3")
            with self.assertRaises(ValueError):
                store.set(10, "xx")
            self.assertIsNone(store.get(10))

    def test_navigation_retains_language_and_lesson(self):
        state = {"language": "ky", "marketing_lesson_stage": "quiz_width_05",
                 "marketing_quiz_step": 2, "mode": "old", "card_data": {"name": "test"}}
        reset_navigation(state)
        self.assertEqual(state, {"language": "ky", "marketing_lesson_stage": "quiz_width_05",
                                 "marketing_quiz_step": 2})

    def test_actions_are_identical_across_languages(self):
        expected = ["nav:ask", "nav:home", "nav:language"]
        for code in LANGUAGES:
            self.assertEqual([payload for _, payload in menu_choices(code)], expected)

    def test_instruction_preserves_market_boundary(self):
        for code in LANGUAGES:
            instruction = language_instruction(code)
            self.assertIn("Do not infer country", instruction)
            self.assertIn("CURRENT/VERIFY/UNKNOWN", instruction)
            self.assertIn("numeric values unchanged", instruction)


if __name__ == "__main__":
    unittest.main()
