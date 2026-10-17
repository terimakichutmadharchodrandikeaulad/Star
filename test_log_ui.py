import asyncio
import os
import shutil
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import app

class TestLogUI(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test_store.json")
        self.store = app.Store(self.db_path)
        app.STORES[12345] = self.store

    def tearDown(self):
        app.STORES.pop(12345, None)
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    async def test_ensure_defaults_and_set_cfg_log_channel(self):
        await app.ensure_defaults(self.store)
        cfg = app.cfg(self.store)
        self.assertIn("log_channel", cfg)
        self.assertEqual(cfg["log_channel"], 0)

        await app.set_cfg(self.store, log_channel=-1001234567890)
        updated_cfg = app.cfg(self.store)
        self.assertEqual(updated_cfg["log_channel"], -1001234567890)

    async def test_log_event_sending(self):
        await app.ensure_defaults(self.store)
        await app.set_cfg(self.store, log_channel=-1001234567890)

        client = MagicMock()
        client.store = self.store
        client.bot_id = 12345
        client.username = "testbot"
        client.send_message = AsyncMock()

        await app.log_event(client, "🔗 TEST EVENT", "Detail message", important=False)

        client.send_message.assert_called()
        log_calls = [call for call in client.send_message.call_args_list if call[0][0] == -1001234567890]
        self.assertTrue(len(log_calls) > 0)
        self.assertIn("TEST EVENT", log_calls[0][0][1])

if __name__ == "__main__":
    unittest.main()
