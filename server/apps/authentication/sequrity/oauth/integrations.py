from .dto import OAuthIntegration


google = OAuthIntegration(
    name='google',
    overwrite=False,
    kwargs=dict(
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
)

OAUTH_INTEGRATIONS = (google, )
