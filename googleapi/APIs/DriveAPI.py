import json
from os import path as os_path
from typing import List, cast, Dict

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
                drive = await google.discover("drive", "v3")
                return await google.as_service_account(
                    method_callable(drive, **method_args)
                )
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error


    #async def _build_path(self):

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

    async def get_children_from_parent(self, drive_id: str, parent_id: str = None, get_all: bool = False) -> List[FileModel]:
        """
        Gets all the files of the drive
        @param drive_id: ID of the drive
        @param parent_id: ID of the parent
        @param get_all: If true, gets all the files of the drive
        @return: List of the files of the drive
        """
        all_items = []
        page_token = None

        search_query = f"parents in '{parent_id}'" if parent_id and not get_all else None

        method_callable = lambda drive, **kwargs: drive.files.list(**kwargs)
        method_args = {"corpora": "drive", "driveId": drive_id, "includeItemsFromAllDrives": True, "orderBy": "folder",
                       "pageSize": 1000,
                       "supportsAllDrives": True,
                       "fields": "nextPageToken, files(id, name, parents)",
                       "q": search_query}
        while True:
            if page_token:
                method_args["pageToken"] = page_token
            response = cast(FilesModel, await self._execute_aiogoogle(method_callable=method_callable, **method_args))
            all_items.extend(response.get("files", []))
            page_token = response.get("nextPageToken", None)
            if not page_token:
                break

        return all_items

    async def build_tree(self, items: List[FileModel], root_id: str) -> List[Dict]:
        nodes = {item['id']: {**item, 'children': []} for item in items}
        tree = []

        for item in items:
            parent_id = item.get('parents', [None])[0]  # Safely get parent or None
            if parent_id == root_id:
                tree.append(nodes[item['id']])
            elif parent_id in nodes:  # Ensure parent exists before appending
                nodes[parent_id]['children'].append(nodes[item['id']])

        return tree

    async def build_paths(self, tree: List[Dict], current_path: str = "") -> List[str]:
        paths = []

        for node in tree:
            node_path = f"{current_path}/{node['name']}".strip("/")
            paths.append(node_path)

            if "children" in node and node["children"]:
                paths.extend(await self.build_paths(node["children"], node_path))

        return paths
