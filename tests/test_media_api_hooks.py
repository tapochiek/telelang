"""Тесты для медиа, API блока, хуков, прав и вебхука."""

import ast
import unittest
from telelang.compiler import TeleCompiler


class TestMediaApiHooks(unittest.TestCase):
    def test_media_and_webhook_emit(self):
        code = '''
        bot "MediaBot" {
            mode = "webhook"
            webhook_url = "https://example.com/telegram/webhook"
            webhook_port = 8443
        }

        command "/photo" {
            send photo "assets/logo.png" {
                caption = "Наш логотип"
            }
        }

        command "/circle" {
            send video_note "assets/circle.mp4"
        }

        command "/doc" {
            send document "report.pdf" {
                caption = "Отчёт за месяц"
            }
        }
        '''
        _, py_code = TeleCompiler.compile_source(code)

        parsed = ast.parse(py_code)
        self.assertIsNotNone(parsed)

        self.assertIn("answer_photo(FSInputFile('assets/logo.png'), caption='Наш логотип')", py_code)
        self.assertIn("answer_video_note(FSInputFile('assets/circle.mp4'))", py_code)
        self.assertIn("answer_document(FSInputFile('report.pdf'), caption='Отчёт за месяц')", py_code)
        self.assertIn("bot.set_webhook('https://example.com/telegram/webhook')", py_code)
        self.assertIn("SimpleRequestHandler", py_code)

    def test_api_block_and_call(self):
        code = '''
        bot "WeatherBot"

        api weather {
            url = "https://api.weather.com/v1/current"
            key = "WEATHER_KEY"
            header "Authorization" = "Bearer 123"
        }

        command "/weather" {
            result = call weather with { q: "Moscow" }
            send "Температура: {result.temp}"
        }
        '''
        _, py_code = TeleCompiler.compile_source(code)

        parsed = ast.parse(py_code)
        self.assertIsNotNone(parsed)

        self.assertIn("async def _call_api_weather", py_code)
        self.assertIn("await _call_api_weather({'q': 'Moscow'})", py_code)

    def test_hooks_and_permissions(self):
        code = '''
        bot "AdminBot"

        before_command {
            log "Поступила команда"
        }

        after_command {
            log "Обработано"
        }

        on_error {
            log_error error
        }

        command "/ban" only admin {
            send "Пользователь заблокирован."
        }
        '''
        _, py_code = TeleCompiler.compile_source(code)

        parsed = ast.parse(py_code)
        self.assertIsNotNone(parsed)

        self.assertIn("class _HookMiddleware(BaseMiddleware):", py_code)
        self.assertIn("logger.info('Поступила команда')", py_code)
        self.assertIn("logger.info('Обработано')", py_code)
        self.assertIn("@router.error()", py_code)
        self.assertIn("BOT_ADMIN_ID", py_code)


    def test_stage4_features_emit(self):
        code = '''
        bot "Stage4Bot"

        ai openai {
            model = "gpt-4o-mini"
        }

        every 15 minutes {
            broadcast "Привет!"
        }

        locales {
            ru { greeting = "Привет" }
            en { greeting = "Hello" }
        }

        command "/test4" {
            send poll "Question" { options = ["1", "2"] }
            send quiz "Quiz" { options = ["A", "B"], correct = 0 }
            send rich { heading "Header" }
            send_invoice { title = "Sub", price = 10 stars }
            stream reply from ai openai "{message.text}"
            react message with "👍"
            remove_reaction message
        }

        on_payment {
            send "Оплачено"
        }
        '''
        _, py_code = TeleCompiler.compile_source(code)
        parsed = ast.parse(py_code)
        self.assertIsNotNone(parsed)

        self.assertIn("async def _ask_ai_openai", py_code)
        self.assertIn("async def _stream_ai_openai", py_code)
        self.assertIn("async def _run_tele_schedulers", py_code)
        self.assertIn("def t(key: str", py_code)
        self.assertIn("await _msg_target.answer_poll", py_code)
        self.assertIn("await _msg_target.answer_invoice", py_code)
        self.assertIn("@router.message(F.successful_payment)", py_code)

    def test_mock_engine_dialog(self):
        from telelang.testing.mock_engine import MockRunner
        import tempfile
        from pathlib import Path

        code = '''
        bot "DialogBot"

        command "/start" {
            send "Привет, {user.name}!"
        }

        on message {
            send "Эхо: {message.text}"
        }
        '''
        with tempfile.NamedTemporaryFile(suffix=".tl", delete=False, mode="w", encoding="utf-8") as f:
            f.write(code)
            f_path = f.name

        try:
            runner = MockRunner(f_path)
            res1 = runner.handle_input("/start")
            self.assertEqual(res1, ["Привет, Тестер!"])
            res2 = runner.handle_input("тестовое сообщение")
            self.assertEqual(res2, ["Эхо: тестовое сообщение"])
        finally:
            Path(f_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
