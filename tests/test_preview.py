import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from lia_languages import LANGUAGES, LanguageStore
from lia_preview import Preview, menu, notice, picker, split_message, validate_config
from lia_preview_copy import COPY, KEYS, copy
from lia_course import CourseStore, load_catalog, revision_token


def update(user_id=10, chat_type="private", payload="nav:ask", message_text="Что такое PV?"):
    message = SimpleNamespace(text=message_text, reply_text=AsyncMock())
    return SimpleNamespace(effective_user=SimpleNamespace(id=user_id),
                           effective_chat=SimpleNamespace(type=chat_type),
                           effective_message=message,
                           callback_query=SimpleNamespace(data=payload, answer=AsyncMock()))


class CopyTests(unittest.TestCase):
    def test_every_language_has_complete_preview_ui(self):
        self.assertEqual(set(COPY), set(LANGUAGES))
        for code in LANGUAGES:
            self.assertEqual(len(COPY[code]), len(KEYS))
            self.assertTrue(all(COPY[code]))
            expected = ["nav:learn", "nav:practice", "nav:quiz", "nav:ask", "nav:sources", "nav:language"]
            if code in {"ru", "uz"}:
                expected.insert(0, "course:menu")
            self.assertEqual([row[0].callback_data for row in menu(code).inline_keyboard], expected)
        self.assertEqual(sum(len(row) for row in picker().inline_keyboard), 9)

    def test_astral_unicode_never_exceeds_telegram_limit(self):
        value = "💚" * 5000 + " Кыргызча O‘zbekcha Тоҷикӣ " * 300
        chunks = list(split_message(value))
        self.assertEqual("".join(chunks), value)
        self.assertTrue(all(len(chunk.encode("utf-16-le")) // 2 <= 3500 for chunk in chunks))

    def test_preview_rejects_production_token_and_missing_settings(self):
        with self.assertRaises(ValueError):
            validate_config({})
        env = {"LIA_PREVIEW_TELEGRAM_TOKEN": "test-token", "OPENAI_API_KEY": "test-key",
               "LIA_LANGUAGE_DB": "/tmp/test.sqlite3", "LIA_PREVIEW_MODEL": "test-model",
               "LIA_PREVIEW_ALLOWED_USER_IDS": "10,20"}
        self.assertEqual(validate_config(env), {10, 20})
        with self.assertRaises(ValueError):
            validate_config(dict(env, TELEGRAM_TOKEN="test-token"))
        with self.assertRaises(ValueError):
            validate_config(dict(env, LIA_PREVIEW_ALLOWED_USER_IDS="0"))
        with self.assertRaises(ValueError):
            validate_config(dict(env, LIA_LANGUAGE_DB="relative.sqlite3"))


class PreviewTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.store = LanguageStore(Path(self.folder.name) / "language.sqlite3")
        self.create = AsyncMock(return_value=SimpleNamespace(output_text="PV — баллы."))
        client = SimpleNamespace(responses=SimpleNamespace(create=self.create))
        self.preview = Preview(self.store, client, "test-model", {10, 20}, "CURRENT: PV is not money")
        self.context = SimpleNamespace(user_data={})

    async def test_first_message_requires_explicit_language_without_api_spend(self):
        event = update()
        await self.preview.message(event, self.context)
        self.create.assert_not_awaited()
        self.assertIn("Choose your language", event.effective_message.reply_text.call_args.args[0])

    async def test_language_switch_preserves_history_and_mode_and_other_user(self):
        self.store.set(20, "tg")
        self.context.user_data = {"mode": "quiz", "history": [{"role": "assistant", "content": "question"}]}
        for code in ("uz", "de"):
            event = update(payload=f"lang:{code}")
            await self.preview.callback(event, self.context)
            self.assertEqual(self.store.get(10), code)
            self.assertEqual(self.context.user_data["mode"], "quiz")
            self.assertEqual(len(self.context.user_data["history"]), 1)
            self.assertIn(notice(code), event.effective_message.reply_text.call_args.args[0])
        self.assertEqual(self.store.get(20), "tg")
        self.create.assert_not_awaited()

    async def test_all_languages_reach_api_with_selected_language_and_sources(self):
        for code in LANGUAGES:
            self.store.set(10, code)
            self.context.user_data = {"mode": "learn"}
            await self.preview.message(update(), self.context)
            request = self.create.call_args.kwargs
            self.assertIn(LANGUAGES[code][1], request["instructions"])
            self.assertIn("CURRENT: PV is not money", request["instructions"])
            self.assertIn("one comprehension question", request["instructions"])
            self.assertEqual(request["input"][-1]["content"], "Что такое PV?")
            self.assertFalse(request["store"])
            self.assertEqual(len(self.context.user_data["history"]), 2)

    async def test_failure_is_localized_and_does_not_corrupt_history(self):
        self.store.set(10, "fr")
        self.create.side_effect = TimeoutError()
        previous = [{"role": "assistant", "content": "question"}]
        self.context.user_data["history"] = previous.copy()
        event = update()
        await self.preview.message(event, self.context)
        self.assertEqual(event.effective_message.reply_text.call_args.args[0], copy("fr", "error"))
        self.assertEqual(self.context.user_data["history"], previous)

    async def test_sources_button_does_not_call_model(self):
        self.store.set(10, "az")
        event = update(payload="nav:sources")
        await self.preview.callback(event, self.context)
        self.create.assert_not_awaited()
        self.assertIn("https://greenleaf-global.com/", event.effective_message.reply_text.call_args.args[0])

    async def test_unknown_callbacks_cannot_change_mode(self):
        self.store.set(10, "en")
        await self.preview.callback(update(payload="nav:delete"), self.context)
        self.assertNotIn("mode", self.context.user_data)
        self.create.assert_not_awaited()

    async def test_unapproved_users_and_groups_cannot_use_model_or_storage(self):
        for event in (update(user_id=30), update(chat_type="supergroup")):
            await self.preview.start(event, self.context)
            await self.preview.message(event, self.context)
            await self.preview.callback(event, self.context)
            if event.effective_chat.type == "private":
                self.assertIn("Telegram ID: 30", event.effective_message.reply_text.call_args.args[0])
                self.assertEqual(event.effective_message.reply_text.await_count, 1)
            else:
                event.effective_message.reply_text.assert_not_awaited()
        self.assertIsNone(self.store.get(30))
        self.create.assert_not_awaited()

    async def test_id_command_works_without_granting_access_or_calling_model(self):
        event = update(user_id=30)
        await self.preview.identify(event, self.context)
        self.assertIn("Telegram ID: 30", event.effective_message.reply_text.call_args.args[0])
        self.assertFalse(self.preview.allowed(event))
        self.assertIsNone(self.store.get(30))
        self.create.assert_not_awaited()

    async def test_course_question_switches_language_without_losing_position(self):
        self.store.set(10, "ru")
        self.preview.courses = CourseStore(self.store.path)
        await self.preview.callback(update(payload="course:open:1"), self.context)
        state = self.preview.courses.get(10)
        await self.preview.callback(update(payload="course:quiz:" + revision_token(self.preview.courses.version, state["revision"])), self.context)
        await self.preview.message(update(message_text="B"), self.context)
        self.assertEqual(self.preview.courses.get(10)["question"], 1)
        event = update(payload="lang:uz")
        await self.preview.callback(event, self.context)
        self.assertEqual(self.preview.courses.get(10)["question"], 1)
        self.assertIn(load_catalog("uz")["lessons"][0]["quiz"][1]["prompt"], event.effective_message.reply_text.call_args.args[0])
        self.create.assert_not_awaited()

    async def test_course_callback_duplicate_is_rejected_in_telegram_adapter(self):
        self.store.set(10, "uz")
        self.preview.courses = CourseStore(self.store.path)
        state = self.preview.courses.act(10, "quiz", expected_revision=0).state
        payload = "course:answer:" + revision_token(self.preview.courses.version, state["revision"]) + ":B"
        await self.preview.callback(update(payload=payload), self.context)
        event = update(payload=payload)
        await self.preview.callback(event, self.context)
        self.assertIn(load_catalog("uz")["ui"]["stale"], event.effective_message.reply_text.call_args.args[0])
        self.assertEqual(self.preview.courses.get(10)["question"], 1)
        self.create.assert_not_awaited()

    async def test_course_without_translation_keeps_language_and_progress(self):
        self.store.set(10, "fr")
        self.preview.courses = CourseStore(self.store.path)
        before = self.preview.courses.get(10)
        event = update(payload="course:open:1")
        await self.preview.callback(event, self.context)
        self.assertEqual(self.store.get(10), "fr")
        self.assertEqual(self.preview.courses.get(10), before)
        self.assertIn(notice("fr"), event.effective_message.reply_text.call_args.args[0])
        self.create.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
