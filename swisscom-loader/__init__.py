import datetime
import logging

import azure.functions as func
from dotenv import find_dotenv, load_dotenv
from oauthlib.oauth2 import BackendApplicationClient
import os
from typing import Optional
from requests_oauthlib import OAuth2Session
from toolz.itertoolz import partition

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


def main(mytimer: func.TimerRequest, document: func.Out[func.Document]) -> None:
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
        "https://api.swisscom.com/layer/heatmaps/demo/grids/municipalities/261",
        headers={"scs-version": "2"},
    )

    if not resp.ok:
        logging.error("Failed to reach Swisscom API")
        return

    tiles = resp.json()["tiles"]

    logging.info("Loaded %d tiles from Swisscom", len(tiles))

    tile_density = {}

    tile_ids = (tile["tileId"] for tile in tiles)
    for chunk in partition(100, tile_ids):
        resp = oauth.get(
            "https://api.swisscom.com/layer/heatmaps/demo/heatmaps/dwell-density/daily/2020-03-28", # TODO this should load data for the previous day instead
            params={"tiles": chunk},
            headers={"scs-version": "2"},
        )

        if not resp.ok:
            logging.error("Failed to reach Swisscom API: %s", resp.json())
            continue

        tile_density.update(
            (tile["tileId"], tile["score"]) for tile in resp.json()["tiles"]
        )

    logging.info("Loaded densitiy for %d tiles from Swisscom", len(tile_density))

    documents = func.DocumentList()
    for tile in tiles:
        tile_id = tile["tileId"]
        if tile_id not in tile_density:
            continue

        density = tile_density[tile_id]
        location = {"type": "Point", "coordinates": [tile["ll"]["x"], tile["ll"]["y"]]}

        documents.append(
            func.Document.from_dict(
                {"tileId": tile_id, "density": density, "location": location}
            )
        )

    document.set(documents)

    logging.info("Finished outputting data")
