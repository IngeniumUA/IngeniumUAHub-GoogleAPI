import json
from os import path as os_path
from typing import List, cast

import aiogoogle.excs
from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import ServiceAccountCreds
from typing_extensions import Callable

from googleapi.TypedDicts.Drive import DriveModel, DrivesModel, FileModel, FilesModel


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

    async def _execute_aiogoogle(self, method_callable: Callable, **method_args):
        try:
            async with Aiogoogle(
                service_account_creds=self.service_account_credentials
            ) as google:
                calendar = await google.discover("drive", "v3")
                return await google.as_service_account(
                    method_callable(calendar, **method_args)
                )
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def get_drives(self) -> List[DriveModel]:
        """
        Gets the drives of the user
        @return: Drives of the user
        """
        method_callable = lambda drive, **kwargs: drive.drives.list()
        return cast(
            DrivesModel, await self._execute_aiogoogle(method_callable=method_callable)
        ).get("drives", [])

    async def get_drive(self, drive_id: str) -> DriveModel:
        """
        Gets the drive of the user
        @param drive_id: ID of the drive
        @return: Drive of the user
        """
        method_callable = lambda drive, **kwargs: drive.drives.get(**kwargs)
        method_args = {"driveId": drive_id}
        return cast(
            DriveModel,
            await self._execute_aiogoogle(
                method_callable=method_callable, **method_args
            ),
        )

    async def delete_drive(self, drive_id: str) -> None:
        """
        Deletes the drive of the user
        @param drive_id: ID of the drive
        @return: Nothing
        """
        method_callable = lambda drive, **kwargs: drive.drives.delete(**kwargs)
        method_args = {"driveId": drive_id}
        await self._execute_aiogoogle(method_callable=method_callable, **method_args)

    async def get_directories(self, drive_id: str) -> List[FileModel]:
        """
        Gets all the files of the drive
        @param drive_id: ID of the drive
        @return: List of the files of the drive
        """
        method_callable = lambda drive, **kwargs: drive.files.list(**kwargs)
        method_args = {
            "driveId": drive_id,
            "corpora": "drive",
            "includeItemsFromAllDrives": True,
            "supportsAllDrives": True,
            "pageSize": 1000,
            "q": "mimeType='application/vnd.google-apps.folder' and trashed=false",
        }
        return cast(
            FilesModel,
            await self._execute_aiogoogle(
                method_callable=method_callable, **method_args
            ),
        ).get("files", [])
