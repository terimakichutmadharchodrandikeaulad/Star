import asyncio
import os
import shutil
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import app

class TestLinkProviderBot(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.factory_db_path = os.path.join(self.tmp_dir, "factory.json")
        self.clone_db_path = os.path.join(self.tmp_dir, "clone_1001.json")

        app.DB_DIR = self.tmp_dir
        app.FACTORY = app.Store(self.factory_db_path)
        self.store = app.Store(self.clone_db_path)
        app.STORES[1001] = self.store

    def tearDown(self):
        app.STORES.pop(1001, None)
        app.SESSIONS.clear()
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    async def test_01_admin_dashboard_access(self):
        """TEST 1: An authorized administrator can open the admin dashboard."""
        await app.ensure_defaults(self.store)
        await self.store.put("admins", "100", {"_id": "100", "role": "owner", "permissions": app.PERMS})

        client = MagicMock()
        client.store = self.store
        client.username = "providerbot"
        client.send_message = AsyncMock()

        await app.show_admin_dashboard(client, 100, uid=100)
        client.send_message.assert_called_once()
        args, kwargs = client.send_message.call_args
        self.assertEqual(args[0], 100)
        self.assertIn("ᴀᴅᴍɪɴ ᴅᴀꜱʜʙᴏᴀʀᴅ", args[1])

    async def test_02_channel_selection_workflow(self):
        """TEST 2: The administrator can select a channel through the supported channel-selection workflow."""
        await app.ensure_defaults(self.store)

        client = MagicMock()
        client.store = self.store
        client.username = "providerbot"

        chat_mock = MagicMock()
        chat_mock.id = -100123456789
        chat_mock.title = "Test Channel"
        chat_mock.username = "testchannel"
        client.get_chat = AsyncMock(return_value=chat_mock)

        bot_mem = MagicMock()
        bot_mem.status = app.CMS.ADMINISTRATOR
        client.get_chat_member = AsyncMock(return_value=bot_mem)

        # Validate channel resolution by username / ID
        ch_doc, err = await app.validate_and_resolve_channel(client, 100, "testchannel")
        self.assertIsNone(err)
        self.assertEqual(ch_doc["channel_id"], -100123456789)
        self.assertEqual(ch_doc["title"], "Test Channel")

    async def test_03_configure_public_link(self):
        """TEST 3: The administrator can configure a public channel link."""
        await app.ensure_defaults(self.store)
        await self.store.put("channels", "-100111", {
            "_id": "-100111", "channel_id": -100111, "title": "Public Channel", "username": "pubchan", "added_by": "100"
        })

        client = MagicMock()
        client.store = self.store
        client.username = "providerbot"

        doc, err = await app.create_provider_link(client, 100, "-100111", "public")
        self.assertIsNone(err)
        self.assertEqual(doc["delivery_mode"], "public")
        self.assertEqual(doc["current_invite_link"], "https://t.me/pubchan")

    async def test_04_configure_private_invite_link(self):
        """TEST 4: The administrator can configure a direct private invite link."""
        await app.ensure_defaults(self.store)
        await self.store.put("channels", "-100222", {
            "_id": "-100222", "channel_id": -100222, "title": "Private Channel", "username": "", "added_by": "100"
        })

        client = MagicMock()
        client.store = self.store
        client.username = "providerbot"
        client.create_chat_invite_link = AsyncMock(return_value=MagicMock(invite_link="https://t.me/+private123"))

        doc, err = await app.create_provider_link(client, 100, "-100222", "private")
        self.assertIsNone(err)
        self.assertEqual(doc["delivery_mode"], "private")
        self.assertEqual(doc["current_invite_link"], "https://t.me/+private123")
        client.create_chat_invite_link.assert_called_once_with(chat_id=-100222, creates_join_request=False, name="Rotated by @providerbot")

    async def test_05_configure_join_request_link(self):
        """TEST 5: The administrator can configure a join-request invite link."""
        await app.ensure_defaults(self.store)
        await self.store.put("channels", "-100333", {
            "_id": "-100333", "channel_id": -100333, "title": "Request Channel", "username": "", "added_by": "100"
        })

        client = MagicMock()
        client.store = self.store
        client.username = "providerbot"
        client.create_chat_invite_link = AsyncMock(return_value=MagicMock(invite_link="https://t.me/+req123"))

        doc, err = await app.create_provider_link(client, 100, "-100333", "join_request")
        self.assertIsNone(err)
        self.assertEqual(doc["delivery_mode"], "join_request")
        self.assertEqual(doc["current_invite_link"], "https://t.me/+req123")
        client.create_chat_invite_link.assert_called_once_with(chat_id=-100333, creates_join_request=True, name="Rotated by @providerbot")

    async def test_06_distinct_and_secure_tokens(self):
        """TEST 6: Each provider URL contains a distinct and secure token."""
        await app.ensure_defaults(self.store)
        await self.store.put("channels", "-100111", {
            "_id": "-100111", "channel_id": -100111, "title": "Channel A", "username": "chana", "added_by": "100"
        })

        client = MagicMock()
        client.store = self.store
        client.username = "providerbot"

        doc1, _ = await app.create_provider_link(client, 100, "-100111", "public")
        doc2, _ = await app.create_provider_link(client, 100, "-100111", "public")

        self.assertNotEqual(doc1["token"], doc2["token"])
        self.assertNotIn("-100111", doc1["token"])
        self.assertNotIn("100", doc1["token"])

    async def test_07_opening_provider_url_returns_link(self):
        """TEST 7: Opening the provider URL returns the correct channel's configured link."""
        await app.ensure_defaults(self.store)
        await self.store.put("channels", "-100111", {
            "_id": "-100111", "channel_id": -100111, "title": "My Channel", "username": "mychan", "added_by": "100"
        })

        client = MagicMock()
        client.store = self.store
        client.username = "providerbot"

        doc, _ = await app.create_provider_link(client, 100, "-100111", "public")

        msg = MagicMock()
        msg.from_user.id = 555
        msg.from_user.first_name = "Alice"
        msg.from_user.username = "alice"
        msg.reply = AsyncMock()

        await app.handle_provider_token_delivery(client, msg, doc["token"])
        msg.reply.assert_called_once()
        args, kwargs = msg.reply.call_args
        kb = kwargs["reply_markup"]
        self.assertEqual(kb.inline_keyboard[0][0].url, "https://t.me/mychan")

    async def test_08_public_link_is_static(self):
        """TEST 8: A public provider link returns the public URL and is not incorrectly treated as a rotating private invite link."""
        await app.ensure_defaults(self.store)
        await self.store.put("channels", "-100111", {
            "_id": "-100111", "channel_id": -100111, "title": "Public Channel", "username": "pubchan", "added_by": "100"
        })

        client = MagicMock()
        client.store = self.store
        client.username = "providerbot"

        doc, _ = await app.create_provider_link(client, 100, "-100111", "public")
        self.assertEqual(doc["next_rotation_at"], 0)

        # Trigger rotation job step -> ensure public link is ignored and not rotated
        app.RUNNING[1001] = client
        with patch.object(client, "create_chat_invite_link", new_callable=AsyncMock) as mock_create:
            await app.rotation_job_step()
            mock_create.assert_not_called()

    async def test_09_private_invite_links_rotate(self):
        """TEST 9: Private invite links rotate at the configured five-minute interval."""
        await app.ensure_defaults(self.store)
        await self.store.put("channels", "-100222", {
            "_id": "-100222", "channel_id": -100222, "title": "Private Channel", "username": "", "added_by": "100"
        })

        client = MagicMock()
        client.store = self.store
        client.username = "providerbot"
        client.create_chat_invite_link = AsyncMock(return_value=MagicMock(invite_link="https://t.me/+link1"))
        client.revoke_chat_invite_link = AsyncMock()

        doc, _ = await app.create_provider_link(client, 100, "-100222", "private")
        self.assertEqual(doc["current_invite_link"], "https://t.me/+link1")

        # Simulate expiration by setting next_rotation_at in past
        rot_key = "-100222:private"
        rot = await self.store.get("rotation_state", rot_key)
        rot["next_rotation_at"] = app.now() - 10
        await self.store.put("rotation_state", rot_key, rot)

        client.create_chat_invite_link = AsyncMock(return_value=MagicMock(invite_link="https://t.me/+link2"))
        app.RUNNING[1001] = client

        await app.rotation_job_step()

        rot_after = await self.store.get("rotation_state", rot_key)
        self.assertEqual(rot_after["current_invite_link"], "https://t.me/+link2")

        # Check that provider link active reference was also updated
        updated_link = await self.store.get("provider_links", doc["_id"])
        self.assertEqual(updated_link["current_invite_link"], "https://t.me/+link2")

    async def test_10_join_request_links_rotate_and_preserve_mode(self):
        """TEST 10: Join-request invite links rotate at the configured five-minute interval while preserving join-request behavior."""
        await app.ensure_defaults(self.store)
        await self.store.put("channels", "-100333", {
            "_id": "-100333", "channel_id": -100333, "title": "Req Channel", "username": "", "added_by": "100"
        })

        client = MagicMock()
        client.store = self.store
        client.username = "providerbot"
        client.create_chat_invite_link = AsyncMock(return_value=MagicMock(invite_link="https://t.me/+req1"))
        client.revoke_chat_invite_link = AsyncMock()

        doc, _ = await app.create_provider_link(client, 100, "-100333", "join_request")

        # Fast forward rotation
        rot_key = "-100333:join_request"
        rot = await self.store.get("rotation_state", rot_key)
        rot["next_rotation_at"] = app.now() - 10
        await self.store.put("rotation_state", rot_key, rot)

        client.create_chat_invite_link = AsyncMock(return_value=MagicMock(invite_link="https://t.me/+req2"))
        app.RUNNING[1001] = client

        await app.rotation_job_step()

        client.create_chat_invite_link.assert_called_with(chat_id=-100333, creates_join_request=True, name="Rotated by @providerbot")
        rot_after = await self.store.get("rotation_state", rot_key)
        self.assertEqual(rot_after["current_invite_link"], "https://t.me/+req2")

    async def test_11_previous_link_revoked_after_replacement(self):
        """TEST 11: The previous rotating invite link is revoked only after its replacement has been generated and saved successfully."""
        await app.ensure_defaults(self.store)
        await self.store.put("channels", "-100222", {
            "_id": "-100222", "channel_id": -100222, "title": "Private", "username": "", "added_by": "100"
        })

        client = MagicMock()
        client.store = self.store
        client.username = "providerbot"
        client.create_chat_invite_link = AsyncMock(return_value=MagicMock(invite_link="https://t.me/+old"))
        client.revoke_chat_invite_link = AsyncMock()

        await app.create_provider_link(client, 100, "-100222", "private")

        rot_key = "-100222:private"
        rot = await self.store.get("rotation_state", rot_key)
        rot["next_rotation_at"] = app.now() - 10
        await self.store.put("rotation_state", rot_key, rot)

        client.create_chat_invite_link = AsyncMock(return_value=MagicMock(invite_link="https://t.me/+new"))
        app.RUNNING[1001] = client

        await app.rotation_job_step()

        client.revoke_chat_invite_link.assert_called_once_with(-100222, "https://t.me/+old")

    async def test_12_disabled_provider_url(self):
        """TEST 12: A disabled provider URL no longer delivers its destination link."""
        await app.ensure_defaults(self.store)
        await self.store.put("channels", "-100111", {
            "_id": "-100111", "channel_id": -100111, "title": "My Channel", "username": "mychan", "added_by": "100"
        })

        client = MagicMock()
        client.store = self.store
        client.username = "providerbot"

        doc, _ = await app.create_provider_link(client, 100, "-100111", "public")
        doc["active"] = False
        await self.store.put("provider_links", doc["_id"], doc)

        msg = MagicMock()
        msg.from_user.id = 555
        msg.reply = AsyncMock()

        await app.handle_provider_token_delivery(client, msg, doc["token"])
        msg.reply.assert_called_once()
        args, _ = msg.reply.call_args
        self.assertIn("Link Disabled", args[0])

    async def test_13_admin_isolation(self):
        """TEST 13: An administrator cannot view or modify another administrator's private management records without permission."""
        await app.ensure_defaults(self.store)
        await self.store.put("channels", "-100111", {
            "_id": "-100111", "channel_id": -100111, "title": "Admin 1 Channel", "username": "chan1", "added_by": "100"
        })

        client = MagicMock()
        client.store = self.store
        client.username = "providerbot"
        client.send_message = AsyncMock()

        doc1, _ = await app.create_provider_link(client, 100, "-100111", "public")

        # Admin 200 attempts to view Admin 100's link detail
        await app.show_link_detail(client, 200, 200, doc1["_id"])
        client.send_message.assert_called_once()
        args, _ = client.send_message.call_args
        self.assertIn("Access Denied", args[1])

    async def test_14_statistics_panel_counts(self):
        """TEST 14: The statistics panel displays consistent counts."""
        await app.ensure_defaults(self.store)
        await self.store.put("channels", "-100111", {
            "_id": "-100111", "channel_id": -100111, "title": "Stat Channel", "username": "statchan", "added_by": "100"
        })

        client = MagicMock()
        client.store = self.store
        client.username = "providerbot"

        doc, _ = await app.create_provider_link(client, 100, "-100111", "public")

        # Simulate 2 visits from user 555 and 1 visit from user 666
        msg555 = MagicMock(); msg555.from_user.id = 555; msg555.reply = AsyncMock()
        msg666 = MagicMock(); msg666.from_user.id = 666; msg666.reply = AsyncMock()

        await app.handle_provider_token_delivery(client, msg555, doc["token"])
        await app.handle_provider_token_delivery(client, msg555, doc["token"])
        await app.handle_provider_token_delivery(client, msg666, doc["token"])

        updated_doc = await self.store.get("provider_links", doc["_id"])
        self.assertEqual(updated_doc["total_visits"], 3)
        self.assertEqual(len(updated_doc["unique_visitors"]), 2)

    async def test_15_resumes_rotation_after_restart(self):
        """TEST 15: The bot resumes its rotation process correctly after a restart."""
        await app.ensure_defaults(self.store)
        await self.store.put("channels", "-100222", {
            "_id": "-100222", "channel_id": -100222, "title": "Private", "username": "", "added_by": "100"
        })

        # Save an overdue rotation state from before restart
        rot_key = "-100222:private"
        await self.store.put("rotation_state", rot_key, {
            "_id": rot_key, "channel_id": -100222, "delivery_mode": "private",
            "current_invite_link": "https://t.me/+old_before_restart",
            "next_rotation_at": app.now() - 500
        })

        client = MagicMock()
        client.store = self.store
        client.username = "providerbot"
        client.create_chat_invite_link = AsyncMock(return_value=MagicMock(invite_link="https://t.me/+resumed_after_restart"))
        client.revoke_chat_invite_link = AsyncMock()

        app.RUNNING[1001] = client

        await app.rotation_job_step()

        rot_after = await self.store.get("rotation_state", rot_key)
        self.assertEqual(rot_after["current_invite_link"], "https://t.me/+resumed_after_restart")

    async def test_16_api_failure_recovery(self):
        """TEST 16: A temporary Telegram API failure does not corrupt the database or destroy the only available valid invite link prematurely."""
        await app.ensure_defaults(self.store)
        await self.store.put("channels", "-100222", {
            "_id": "-100222", "channel_id": -100222, "title": "Private", "username": "", "added_by": "100"
        })

        client = MagicMock()
        client.store = self.store
        client.username = "providerbot"
        client.create_chat_invite_link = AsyncMock(return_value=MagicMock(invite_link="https://t.me/+valid_link"))

        await app.create_provider_link(client, 100, "-100222", "private")

        # Simulate API failure on rotation
        rot_key = "-100222:private"
        rot = await self.store.get("rotation_state", rot_key)
        rot["next_rotation_at"] = app.now() - 10
        await self.store.put("rotation_state", rot_key, rot)

        client.create_chat_invite_link = AsyncMock(side_effect=app.RPCError("FloodWait"))
        app.RUNNING[1001] = client

        await app.rotation_job_step()

        # Check current valid link remains preserved
        rot_after = await self.store.get("rotation_state", rot_key)
        self.assertEqual(rot_after["current_invite_link"], "https://t.me/+valid_link")
        self.assertIn("FloodWait", rot_after["rotation_error"])

    async def test_17_anime_features_removed(self):
        """TEST 17: All anime upload functionality has been removed."""
        self.assertFalse(hasattr(app, "cmd_upload"))
        self.assertFalse(hasattr(app, "cmd_edit"))
        self.assertFalse(hasattr(app, "cmd_delete"))
        self.assertFalse(hasattr(app, "cmd_seasonend"))
        self.assertFalse(hasattr(app, "cmd_coming"))
        self.assertNotIn("upload", app.PERMS)

    async def test_18_unrelated_features_intact(self):
        """TEST 18: Existing unrelated configuration and working features remain intact."""
        await app.ensure_defaults(self.store)
        self.assertIn("cfg", self.store.c("settings"))
        self.assertIn("start", self.store.c("settings"))
        self.assertTrue(callable(app.cmd_clone))
        self.assertTrue(callable(app.cmd_supreme))
        self.assertTrue(callable(app.cmd_broadcast))

if __name__ == "__main__":
    unittest.main()
