"""Regression tests for reauth before setup and while a feeder is loaded."""

from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from custom_components.petkit_feeder import async_update_options, config_flow
from custom_components.petkit_feeder.pypetkitapi.exceptions import (
    PetkitAuthenticationError,
    PetkitTimeoutError,
)


class ReauthTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.flow = config_flow.PetkitConfigFlow()
        self.flow.flow_id = "repair"
        self.flow.handler = config_flow.DOMAIN
        self.flow.context = {"source": "reauth", "entry_id": "first"}
        self.flow.hass = Mock()
        self.entries = self.flow.hass.config_entries
        self.entry = SimpleNamespace(
            entry_id="first", title="Feeder", update_listeners=[],
            data={"username": "owner", "password": "old", "device_id": "21", "region": "EU"},
        )
        self.entries.async_get_entry.return_value = self.entry
        self.entries.async_get_known_entry.return_value = self.entry
        self.client = self.enterContext(patch.object(config_flow, "PetKitClient"))
        self.login = self.client.return_value.login = AsyncMock()

    async def test_retry_then_recover_failed_entry(self):
        form = await self.flow.async_step_reauth(self.entry.data)
        self.assertEqual(form["step_id"], "reauth_confirm")
        self.assertEqual(form["description_placeholders"]["username"], "owner")
        for error, code in (
            (PetkitAuthenticationError(), "invalid_auth"),
            (PetkitTimeoutError(), "connection_failed"),
        ):
            self.login.side_effect = error
            result = await self.flow.async_step_reauth_confirm({"password": "wrong"})
            self.assertEqual(result["errors"], {"base": code})
            self.entries.async_update_entry.assert_not_called()
            self.entries.async_reload.assert_not_called()
        self.login.side_effect = None
        result = await self.flow.async_step_reauth_confirm({"password": "new"})
        self.assertEqual(result["reason"], "reauth_successful")
        credentials = self.client.call_args.kwargs
        self.assertEqual((credentials["username"], credentials["region"]), ("owner", "EU"))
        self.entries.async_update_entry.assert_called_once_with(
            self.entry, data={**self.entry.data, "password": "new"}
        )
        self.entries.async_reload.assert_called_once_with(self.entry.entry_id)

    async def test_loaded_entry_listener_handles_changed_password(self):
        self.entry.update_listeners.append(async_update_options)
        # HA can start the listener and unload the entry before the update call returns.
        self.entries.async_update_entry.side_effect = lambda *a, **kw: self.entry.update_listeners.clear()
        result = await self.flow.async_step_reauth_confirm({"password": "new"})
        self.assertEqual(result["reason"], "reauth_successful")
        self.entries.async_reload.assert_not_called()

    async def test_expired_session_with_unchanged_password_still_reloads(self):
        self.entry.update_listeners.append(async_update_options)
        result = await self.flow.async_step_reauth_confirm({"password": "old"})
        self.assertEqual(result["reason"], "reauth_successful")
        self.entries.async_reload.assert_called_once_with(self.entry.entry_id)
