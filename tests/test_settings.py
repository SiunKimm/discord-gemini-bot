import os
import unittest

os.environ.setdefault("DISCORD_BOT_TOKEN", "test-discord-token")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")

from config import settings


class SettingsTests(unittest.TestCase):
    def test_required_env_returns_value(self) -> None:
        os.environ["TEMP_REQUIRED_ENV"] = "ok"
        self.assertEqual(settings._get_required_env("TEMP_REQUIRED_ENV"), "ok")

    def test_required_env_raises_when_missing(self) -> None:
        if "TEMP_REQUIRED_ENV_MISSING" in os.environ:
            del os.environ["TEMP_REQUIRED_ENV_MISSING"]

        with self.assertRaises(RuntimeError):
            settings._get_required_env("TEMP_REQUIRED_ENV_MISSING")

    def test_constants_loaded(self) -> None:
        self.assertEqual(settings.DISCORD_TOKEN, "test-discord-token")
        self.assertEqual(settings.GEMINI_API_KEY, "test-gemini-key")


if __name__ == "__main__":
    unittest.main()
