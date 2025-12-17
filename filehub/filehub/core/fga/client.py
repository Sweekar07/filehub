import os
from openfga_sdk import ClientConfiguration, OpenFgaClient
from openfga_sdk.credentials import Credentials, CredentialConfiguration

def get_fga_client() -> OpenFgaClient:
    credentials = Credentials(
      method="client_credentials",
      configuration=CredentialConfiguration(
        api_issuer=os.environ.get("api_issuer"),
        api_audience=os.environ.get("api_audience"),
        client_id=os.environ.get("client_id"),
        client_secret=os.environ.get("client_secret"),
      )
    )

    config = ClientConfiguration(
        api_url=os.environ["FGA_API_URL"],
        store_id=os.environ["FGA_STORE_ID"],
        authorization_model_id=os.environ["FGA_AUTHZ_MODEL_ID"],
        credentials=credentials,
    )

    return OpenFgaClient(config)
