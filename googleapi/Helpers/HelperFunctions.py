import json
from typing import Callable, Dict, List

import aiogoogle
from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import ServiceAccountCreds


def build_service_account_credentials(service_file: json, scopes: List[str], subject: str) -> ServiceAccountCreds:
    """
    @return: Returns ServiceAccountCreds from aiogoogle
    """
    with open(service_file, "r") as f:
        service_account_key = json.load(f)
    credentials = ServiceAccountCreds(
        scopes=scopes, **service_account_key, subject=subject
    )
    return credentials


async def execute_aiogoogle(method_callable: Callable, service_account_credentials: ServiceAccountCreds, api_name: str, api_version: str, **method_args: Dict):
    try:
        async with Aiogoogle(
                service_account_creds=service_account_credentials
        ) as google:
            api = await google.discover(api_name, api_version)
            return await google.as_service_account(
                method_callable(api, **method_args)
            )
    except aiogoogle.excs.HTTPError as error:
        raise Exception(f"Aiogoogle error: {error}") from error
