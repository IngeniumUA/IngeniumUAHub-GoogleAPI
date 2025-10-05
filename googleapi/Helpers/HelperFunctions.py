import json
import os
from typing import Callable, Dict, List

import aiofiles
import aiogoogle
from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import ServiceAccountCreds
from fastapi import HTTPException
from google.oauth2 import service_account
from googleapiclient.discovery import build


async def build_service_account_credentials(
    service_file: json, scopes: List[str], subject: str
) -> ServiceAccountCreds:
    """
    @param service_file: Service account credentials json file
    @param scopes: Scopes of the API
    @param subject: Subject of the API
    @return: Returns ServiceAccountCreds from aiogoogle
    """
    # Check if its the file content or path to the file
    if isinstance(service_file, dict):
        service_account_key = service_file
    elif isinstance(service_file, os.PathLike):
        async with aiofiles.open(service_file, "r") as file:
            service_account_key = json.loads(await file.read())
    else:
        raise TypeError(
            f"Expected service_file to be a dict or a file path (str), got {type(service_file).__name__}"
        )
    credentials = ServiceAccountCreds(
        scopes=scopes, **service_account_key, subject=subject
    )
    return credentials


async def execute_aiogoogle(
    method_callable: Callable,
    service_account_credentials: ServiceAccountCreds,
    api_name: str,
    api_version: str,
    **method_args: Dict,
):
    """
    @param method_callable: The method called from the API
    @param service_account_credentials: Service account credentials
    @param api_name: Name of the API
    @param api_version: Version of the API
    @param method_args: Arguments passed to the API
    @return: Result of the API call
    """
    try:
        async with Aiogoogle(
            service_account_creds=service_account_credentials
        ) as google:
            print("Inside Aiogoogle context")

            api = await google.discover(api_name, api_version, disco_doc_ver=2)
            print("Discovery complete")
            print(api)
            return await google.as_service_account(method_callable(api, **method_args))
    except aiogoogle.excs.HTTPError as error:
        raise HTTPException(
            status_code=error.res.status_code,
            detail={
                "message": "Aiogoogle API request failed.",
                "error": error.res.json,
            },
        ) from error


def synchronous_build_service_account_credentials(
    service_file: json, scopes: List[str], subject: str
):
    """
    @param service_file: Service account credentials json file
    @param scopes: Scopes of the API
    @param subject: Subject of the API
    @return: Returns credentials from google
    """
    credentials = service_account.Credentials.from_service_account_info(
        info=service_file, scopes=scopes, subject=subject
    )
    return credentials


def synchronous_build_service(api_name: str, api_version: str, credentials):
    service = build(version=api_version, serviceName=api_name, credentials=credentials)
    return service
