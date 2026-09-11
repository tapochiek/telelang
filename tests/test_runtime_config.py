"""Тесты разрешения конфигурации и токенов (ConfigResolver)."""

import os
import unittest
from pathlib import Path
from telelang.errors import TeleLangConfigError
from telelang.runtime.config import ConfigResolver


class TestConfigResolver(unittest.TestCase):
    def setUp(self):
        self.old_env = os.environ.get("BOT_TOKEN")
        if "BOT_TOKEN" in os.environ:
            del os.environ["BOT_TOKEN"]

    def tearDown(self):
        if self.old_env is not None:
            os.environ["BOT_TOKEN"] = self.old_env
        elif "BOT_TOKEN" in os.environ:
            del os.environ["BOT_TOKEN"]

    def test_cli_token_priority(self):
        os.environ["BOT_TOKEN"] = "123456:env_token"
        token = ConfigResolver.resolve_bot_token(
            cli_token="123456:cli_token_value",
            code_token="123456:code_token_value",
        )
        self.assertEqual(token, "123456:cli_token_value")

    def test_code_token_priority(self):
        os.environ["BOT_TOKEN"] = "123456:env_token"
        token = ConfigResolver.resolve_bot_token(
            cli_token=None,
            code_token="123456:code_token_value",
        )
        self.assertEqual(token, "123456:code_token_value")

    def test_token_from_code_in_tl_file(self):
        import tempfile
        from telelang.compiler import TeleCompiler
        code = '''
        token = "123456:token_from_code"
        bot "MyBot"
        command "/start" { send "Привет!" }
        '''
        with tempfile.NamedTemporaryFile(suffix=".tl", mode="w", encoding="utf-8", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            program, _ = TeleCompiler.compile_file(temp_path)
            code_token = None
            for decl in program.declarations:
                from telelang.parser.ast_nodes import ConfigDecl
                if isinstance(decl, ConfigDecl) and decl.key == "token":
                    code_token = decl.value
            token = ConfigResolver.resolve_bot_token(code_token=code_token)
            self.assertEqual(token, "123456:token_from_code")
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_env_var_fallback(self):
        os.environ["BOT_TOKEN"] = "123456:my_secret_bot_token"
        token = ConfigResolver.resolve_bot_token()
        self.assertEqual(token, "123456:my_secret_bot_token")

    def test_missing_token_raises_helpful_error(self):
        with self.assertRaises(TeleLangConfigError) as ctx:
            ConfigResolver.resolve_bot_token()
        self.assertIn("Не найден токен Telegram-бота", str(ctx.exception))
        self.assertIn("BOT_TOKEN=", str(ctx.exception))
        self.assertIn("--token", str(ctx.exception))

    def test_invalid_token_raises_config_error(self):
        from telelang.runtime.runner import BotRunner
        tl_file = Path(__file__).parent.parent / "examples" / "01_hello_bot.tl"
        with self.assertRaises(TeleLangConfigError) as ctx:
            BotRunner.run_file(tl_file, cli_token="invalid_token")
        self.assertIn("Некорректный формат токена Telegram", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
