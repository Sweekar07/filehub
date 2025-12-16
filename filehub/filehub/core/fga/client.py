import os
from openfga_sdk import ClientConfiguration, OpenFgaClient
from openfga_sdk.credentials import Credentials, CredentialConfiguration

def get_fga_client() -> OpenFgaClient:
    credentials = Credentials(
        method="api_token",
        configuration=CredentialConfiguration(
            api_token=os.environ["FGA_API_TOKEN"]
        )
    )

    config = ClientConfiguration(
        api_url=os.environ["FGA_API_URL"],
        store_id=os.environ["FGA_STORE_ID"],
        authorization_model_id=os.environ["FGA_AUTHZ_MODEL_ID"],
        credentials=credentials,
    )

    return OpenFgaClient(config)
