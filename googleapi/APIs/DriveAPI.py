import json
from os import path as os_path
from typing import List, cast

import aiogoogle.excs
from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import ServiceAccountCreds
from typing_extensions import Callable

from googleapi.TypedDicts.Drive import DriveModel, DrivesModel


class Drive:
    """
    Implements the Google Drive API to manipulate Google Drive.
    """

    def __init__(self, service_file_path: str, subject: str) -> None:
        """
        @param service_file_path: Path to the service account credentials file
        @param subject: Subject who owns the drive
        """
        self.scopes = ["https://www.googleapis.com/auth/drive"]
        self.timeZone = "Europe/Brussels"
        self.subject = subject

        if not os_path.exists(service_file_path):
            raise Exception("Service account json path does not exist")

        self.serviceFilePath = service_file_path
        self.service_account_credentials = self._build_service_account_credentials()

    def _build_service_account_credentials(self) -> ServiceAccountCreds:
        """
        @return: Returns ServiceAccountCreds from aiogoogle
        """
        service_account_key = json.load(open(self.serviceFilePath))
        credentials = ServiceAccountCreds(
            scopes=self.scopes, **service_account_key, subject=self.subject
        )
        return credentials

    async def _execute_aiogoogle(self, function: Callable, **kwargs):
        try:
            async with Aiogoogle(
                service_account_creds=self.service_account_credentials
            ) as google:
                calendar = await google.discover("drive", "v3")
                return await google.as_service_account(function(calendar, **kwargs))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def get_drives(self) -> List[DriveModel]:
        """
        Gets the drives of the user
        @return: Drives of the user
        """
        def function(drive): return drive.drives.list()
        return cast(DrivesModel, await self._execute_aiogoogle(function)).get("drives", [])

    async def get_drive(self, drive_id: str) -> DriveModel:
        """
        Gets the drive of the user
        @param drive_id: ID of the drive
        @return: Drive of the user
        """
        def function(drive, **kwargs): return drive.drives.get(**kwargs)
        kwargs = {"driveId": drive_id}
        return cast(DriveModel, await self._execute_aiogoogle(function, **kwargs))

    async def delete_drive(self, drive_id) -> None:
        """
        Deletes the drive of the user
        @param drive_id: ID of the drive
        @return: Nothing
        """
        def function(drive, **kwargs): drive.drives.delete(**kwargs)
        kwargs = {"driveId": drive_id}
        await self._execute_aiogoogle(function, **kwargs)
