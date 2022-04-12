from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

from .dto import OAuthIntegration


def register_integrations(config: Config, *integrations: OAuthIntegration) -> OAuth:
    client = OAuth(config)

    for integration in integrations:
        client.register(
            name=integration.name,
            overwrite=integration.overwrite,
            **integration.kwargs
        )

    return client
