"""Serve the bundled PetKit card and register its Lovelace resource."""

from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import urlsplit

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

CARD_FILENAME = "petkit-feeder-card.js"
CARD_PATH = Path(__file__).parent / "www" / CARD_FILENAME
CARD_URL = f"/petkit_feeder/{CARD_FILENAME}"
LEGACY_CARD_PATHS = {
    f"/hacsfiles/petkit-feeder-card/{CARD_FILENAME}",
    f"/local/community/petkit-feeder-card/{CARD_FILENAME}",
    f"/local/{CARD_FILENAME}",
}


class PetkitCardView(HomeAssistantView):
    """Serve the card module from a URL that works across supported HA versions."""

    url = CARD_URL
    name = "petkit_feeder:card"
    requires_auth = False

    async def get(self, request: web.Request) -> web.FileResponse:
        """Allow browsers to revalidate the module after integration upgrades."""
        return web.FileResponse(
            CARD_PATH,
            headers={"Content-Type": "text/javascript", "Cache-Control": "no-cache"},
        )


async def async_setup_card(hass: HomeAssistant) -> None:
    """Register the bundled module without replacing user-managed resources."""
    lovelace = hass.data.get("lovelace")
    if lovelace is None:
        return

    if not await hass.async_add_executor_job(CARD_PATH.is_file):
        _LOGGER.debug("Bundled card is missing. Install the integration release ZIP.")
        return

    hass.http.register_view(PetkitCardView())

    # Older HA releases store Lovelace state in a dict rather than LovelaceData.
    resources = lovelace["resources"] if isinstance(lovelace, dict) else lovelace.resources
    if not isinstance(resources, ResourceStorageCollection):
        # YAML resources are owned by configuration.yaml.
        return

    # Core versions with lazy loading must read existing resources before writing.
    if not resources.loaded:
        await resources.async_get_info()

    paths = {urlsplit(item["url"]).path for item in resources.async_items()}
    if CARD_URL in paths:
        return
    if LEGACY_CARD_PATHS & paths:
        _LOGGER.info(
            "Remove the standalone PetKit card resource and restart Home Assistant "
            "to switch to the bundled card"
        )
        return

    await resources.async_create_item({"url": CARD_URL, "res_type": "module"})
