"""Config flow for sentry integration."""
import logging

from sentry_sdk.utils import BadDsn, Dsn
import voluptuous as vol

from homeassistant import config_entries, core
from homeassistant.core import callback

from .const import CONF_DSN, CONF_ENVIRONMENT, DOMAIN  # pylint: disable=unused-import

_LOGGER = logging.getLogger(__name__)

DEFAULT_SCHEMA = vol.Schema({vol.Required(CONF_DSN): str})


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the DSN input.

    Data has the keys from the schema with values provided by the user.
    """
    # validate the dsn
    Dsn(data["dsn"])

    return {"title": "Sentry"}


class SentryMixin:
    """Helper mixin for uniform form handling."""

    async def sentry_async_step(self, step_id, schema, user_input=None):
        """Handle user input and validation errors."""
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                return self.async_create_entry(title=info["title"], data=user_input)
            except BadDsn:
                errors["dsn"] = "bad_dsn"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(step_id=step_id, data_schema=schema, errors=errors)


class SentryConfigFlow(SentryMixin, config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Sentry config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle a user config flow."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        return await self.sentry_async_step("user", DEFAULT_SCHEMA, user_input)

    async def async_step_import(self, import_config):
        """Import a config entry from configuration.yaml."""
        return await self.async_step_user(import_config)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return SentryOptionsFlow(config_entry)


class SentryOptionsFlow(SentryMixin, config_entries.OptionsFlow):
    """Handle Sentry options."""

    def __init__(self, config_entry):
        """Initialize the options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage Sentry options."""
        options = {
            vol.Required(CONF_DSN, default=self.config_entry.data.get(CONF_DSN)): str,
            vol.Optional(
                CONF_ENVIRONMENT,
                default=self.config_entry.options.get(CONF_ENVIRONMENT),
            ): str,
        }
        return await self.sentry_async_step("init", vol.Schema(options), user_input)
