import datetime
import logging

import azure.functions as func
from dotenv import find_dotenv, load_dotenv
from oauthlib.oauth2 import BackendApplicationClient
import os
from typing import Optional
from requests_oauthlib import OAuth2Session

TOKEN_URL = "https://consent.swisscom.com/o/oauth2/token"


def get_vars() -> Optional[bool]:
    """Collect the needed keys to call the APIs and access storage accounts.

    Returns:
        bool: Optional - if dotenv file is present then this is loaded, else the
        vars are used directly from the system env
    """
    try:
        dotenv_path = find_dotenv(".env")
        logging.info("Dotenv located, loading vars from local instance")
        return load_dotenv(dotenv_path)

    except:
        logging.info("Loading directly from system")


def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = (
        datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    )

    get_vars()

    # Read the secrets from the environment
    client_id = os.environ.get("SWISSCOM_CLIENT_ID")
    client_secret = os.environ.get("SWISSCOM_CLIENT_SECRET")

    # See https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html#backend-application-flow.
    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)

    # Fetch an access token.
    oauth.fetch_token(
        token_url=TOKEN_URL, client_id=client_id, client_secret=client_secret
    )

    # Use the access token to query an endpoint.
    resp = oauth.get(
        "https://api.swisscom.com/layer/heatmaps/demo/grids/postal-code-areas/3097",
        headers={"scs-version": "2"},
    )
    logging.info(resp.json())
