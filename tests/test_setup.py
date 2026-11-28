"""Regression tests for setup forms, diagnostics and feeder timestamps."""

import json
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from homeassistant import loader
from homeassistant.components.diagnostics import REDACTED
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from voluptuous_serialize import convert

from custom_components import petkit_feeder
from custom_components.petkit_feeder import config_flow, coordinator, diagnostics
from custom_components.petkit_feeder.const import DOMAIN
from custom_components.petkit_feeder.pypetkitapi.exceptions import PetkitAuthenticationError
from custom_components.petkit_feeder.utils.timezone import async_get_feeder_time_zone


class SetupTests(IsolatedAsyncioTestCase):
    async def test_password_field_in_initial_and_retry_forms(self):
        flow = config_flow.PetkitConfigFlow()
        flow.flow_id = "setup"
        flow.handler = DOMAIN
        flow.context = {"source": "user"}
        credentials = {"username": "owner", "password": "sample-secret", "region": "EU"}

        initial = await flow.async_step_user()
        with patch.object(config_flow, "_async_login", side_effect=PetkitAuthenticationError):
            retry = await flow.async_step_user(credentials)
        self.assertEqual(retry["errors"], {"base": "invalid_auth"})
        for form in (initial, retry):
            schema = convert(form["data_schema"], custom_serializer=cv.custom_serializer)
            password = next(field for field in schema if field["name"] == "password")
            self.assertEqual(password["selector"]["text"]["type"], "password")
            self.assertNotIn("default", password)
            self.assertNotIn(credentials["password"], json.dumps(schema))

    async def test_diagnostics_redact_account_fields(self):
        entry = Mock(entry_id="entry")
        entry.as_dict.return_value = {
            "title": "Private Owner (ID: 48912)",
            "unique_id": "private-id",
            "data": {
                "user_name": "Private Owner",
                "user_id": 48912,
                "username": "private-login",
                "password": "secret",
                "region": "EU",
            },
        }
        hass = SimpleNamespace(data={DOMAIN: {"entry": SimpleNamespace(data={})}})
        report = await diagnostics.async_get_config_entry_diagnostics(hass, entry)
        exported = report["entry"]
        self.assertEqual(exported["title"], REDACTED)
        self.assertEqual(exported["unique_id"], REDACTED)
        for field in ("user_name", "user_id", "username", "password"):
            self.assertEqual(exported["data"][field], REDACTED)
        self.assertEqual(exported["data"]["region"], "EU")

    async def test_setup_and_feeding_times_across_dst(self):
        hass = HomeAssistant(self.enterContext(TemporaryDirectory()))
        loader.async_setup(hass)
        hass.config.time_zone = "America/New_York"
        hass.config_entries = Mock(async_forward_entry_setups=AsyncMock())
        entry = Mock(
            entry_id="feeder",
            state=ConfigEntryState.SETUP_IN_PROGRESS,
            data={"username": "owner", "password": "test", "device_id": "21", "region": "CN"},
            options={},
        )
        with patch.object(coordinator, "PetKitClient") as client:
            api = client.return_value
            api._session = None
            api.login = AsyncMock()
            api.get_devices_data = AsyncMock()
            api.petkit_entities = {
                21: config_flow.Feeder.model_construct(id=21, name="Feeder", type="d4")
            }
            self.assertTrue(await petkit_feeder.async_setup_entry(hass, entry))
        feeder = hass.data[DOMAIN][entry.entry_id]
        self.addAsyncCleanup(feeder.cleanup)
        metadata = await loader.async_get_integration(hass, DOMAIN)
        self.assertEqual(feeder.version, str(metadata.version))
        self.assertEqual(client.call_args.kwargs["timezone"], "America/New_York")
        self.assertEqual(str(feeder.get_current_datetime().tzinfo), "America/New_York")
        for hour, expected in (("06", "01:30:00.000-0500"), ("07", "03:30:00.000-0400")):
            utc = f"2026-03-08T{hour}:30:00.000+0000"
            item = SimpleNamespace(time=3600, state=SimpleNamespace(completed_at=utc))
            record = feeder._parse_feed_item(item)
            self.assertEqual(record["completed_at"], "2026-03-08T" + expected)
            self.assertEqual(record["completed_at_utc"], utc)

    async def test_utc_and_region_fallback(self):
        hass = SimpleNamespace(config=SimpleNamespace(time_zone="UTC"))
        self.assertEqual(str(await async_get_feeder_time_zone(hass, "CN")), "UTC")
        hass.config.time_zone = ""
        self.assertEqual(str(await async_get_feeder_time_zone(hass, "EU")), "Europe/Berlin")
