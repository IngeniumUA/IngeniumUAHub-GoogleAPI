import json
from typing import List, cast, Dict

from googleapi.Helpers.HelperFunctions import (
    build_service_account_credentials,
    execute_aiogoogle,
)
from googleapi.TypedDicts.Drive import DriveModel, DrivesModel, FileModel, FilesModel


class Drive:
    """
    Implements the Google Drive API to manipulate Google Drive.
    """

    def __init__(self) -> None:
        self.api_name = "drive"
        self.api_version = "v3"

    async def _async_init(self, service_file: json, subject: str):
        """
        @param service_file: Service account credentials file
        @param subject: Subject who owns the drive
        """
        self.service_account_credentials = await build_service_account_credentials(
            service_file=service_file,
            scopes=["https://www.googleapis.com/auth/drive"],
            subject=subject,
        )

    async def get_drives(self) -> List[DriveModel]:
        """
        Gets the drives of the user
        @return: Drives of the user
        """
        method_callable = lambda drive, **kwargs: drive.drives.list()
        return cast(
            DrivesModel,
            await execute_aiogoogle(
                method_callable=method_callable,
                service_account_credentials=self.service_account_credentials,
                api_name=self.api_name,
                api_version=self.api_version,
            ),
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
            await execute_aiogoogle(
                method_callable=method_callable,
                service_account_credentials=self.service_account_credentials,
                api_name=self.api_name,
                api_version=self.api_version,
                **method_args,
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
        await execute_aiogoogle(
            method_callable=method_callable,
            service_account_credentials=self.service_account_credentials,
            api_name=self.api_name,
            api_version=self.api_version,
            **method_args,
        )

    async def get_file(self, file_id: str) -> FileModel:
        """
        Gets the files
        :param file_id: ID of the file
        :return: File
        """
        method_callable = lambda drive, **kwargs: drive.files.get(**kwargs)
        method_args = {
            "fileId": file_id,
            "supportsAllDrives": True,
            "fields": "id, name, parents",
        }
        return cast(
            FileModel,
            await execute_aiogoogle(
                method_callable=method_callable,
                service_account_credentials=self.service_account_credentials,
                api_name=self.api_name,
                api_version=self.api_version,
                **method_args,
            ),
        )

    async def get_children_from_parent(
        self, drive_id: str, parent_id: str = None, get_all: bool = False
    ) -> List[FileModel]:
        """
        Gets all the files of the drive
        @param drive_id: ID of the drive
        @param parent_id: ID of the parent
        @param get_all: If true, gets all the files of the drive
        @return: List of the files of the drive
        """
        all_items = []
        page_token = None

        search_query = (
            f"parents in '{parent_id}'" if parent_id and not get_all else None
        )

        method_callable = lambda drive, **kwargs: drive.files.list(**kwargs)
        method_args = {
            "corpora": "drive",
            "driveId": drive_id,
            "includeItemsFromAllDrives": True,
            "orderBy": "folder",
            "pageSize": 1000,
            "supportsAllDrives": True,
            "fields": "nextPageToken, files(id, name, parents)",
            "q": search_query,
        }
        while True:
            if page_token:
                method_args["pageToken"] = page_token
            response = cast(
                FilesModel,
                await execute_aiogoogle(
                    method_callable=method_callable,
                    service_account_credentials=self.service_account_credentials,
                    api_name=self.api_name,
                    api_version=self.api_version,
                    **method_args,
                ),
            )
            all_items.extend(response.get("files", []))
            page_token = response.get("nextPageToken", None)
            if not page_token:
                break

        return all_items

    async def build_tree(self, items: List[FileModel], root_id: str) -> List[Dict]:
        """
        Builds a tree out of given items from the drive
        :param items: List of the items to make a tree of
        :param root_id: ID of the root
        :return: Tree as a list of dictionaries
        """
        nodes = {item["id"]: {**item, "children": []} for item in items}
        tree = []

        for item in items:
            parent_id = item.get("parents", [None])[0]  # Safely get parent or None
            if parent_id == root_id:
                tree.append(nodes[item["id"]])
            elif parent_id in nodes:  # Ensure parent exists before appending
                nodes[parent_id]["children"].append(nodes[item["id"]])

        return tree

    async def build_paths(self, tree: List[Dict], current_path: str = "") -> List[str]:
        """
        Builds paths out of the given tree
        :param tree: The tree to build the paths of
        :param current_path: The current path
        :return: List of paths
        """
        paths = []

        for node in tree:
            node_path = f"{current_path}/{node['name']}".strip("/")
            paths.append(node_path)

            if "children" in node and node["children"]:
                paths.extend(await self.build_paths(node["children"], node_path))

        return paths

    async def download_file(self, file_id: str) -> bytes:
        """
        Downloads a file from the drive
        :param file_id: ID of the file to download
        :return: File as bytes
        """
        method_callable = lambda drive, **kwargs: drive.files.get(**kwargs)
        method_args = {"fileId": file_id, "alt": "media"}

        return cast(
            bytes,
            await execute_aiogoogle(
                method_callable=method_callable,
                service_account_credentials=self.service_account_credentials,
                api_name=self.api_name,
                api_version=self.api_version,
                **method_args,
            ),
        )

    async def upload_file(
        self,
        drive_id: str,
        parent_id: str,
        mime_type: str,
        file_content: bytes,
        file_name: str,
        upload_type: str = "multipart",
    ) -> FileModel:
        """
        Uploads a file to the drive
        :param drive_id: ID of the drive
        :param parent_id: ID of the parent
        :param mime_type: Mime type of the file
        :param file_content: File content of the file as bytes
        :param file_name: Name of the file
        :param upload_type: Optional (media, multipart, resumable), check: https://developers.google.com/drive/api/reference/rest/v3/files/create
        :return: The file
        """
        method_callable = lambda drive, **kwargs: drive.files.create(**kwargs)

        file_metadata = {
            "name": file_name,
            "mimeType": mime_type,
            "parents": [parent_id],
            "driveId": drive_id,
        }

        method_args = {
            "uploadType": upload_type,
            "supportsAllDrives": True,
            "json": file_metadata,
            "upload_file": file_content,
        }

        return cast(
            FileModel,
            await execute_aiogoogle(
                method_callable=method_callable,
                service_account_credentials=self.service_account_credentials,
                api_name=self.api_name,
                api_version=self.api_version,
                **method_args,
            ),
        )

    async def delete_file(self, file_id: str) -> None:
        """
        Deletes a file from the drive
        :param file_id: ID of the file to delete
        :return: None
        """
        method_callable = lambda drive, **kwargs: drive.files.delete(**kwargs)
        method_args = {"fileId": file_id, "supportsAllDrives": True}
        await execute_aiogoogle(
            method_callable=method_callable,
            service_account_credentials=self.service_account_credentials,
            api_name=self.api_name,
            api_version=self.api_version,
            **method_args,
        )

    async def change_file_name(
        self, file_id: str, file_name: str, upload_type: str = "multipart"
    ) -> FileModel:
        """
        Changes the file name
        :param file_id: ID of the file to change
        :param file_name: New name of the file, type needs to be specified
        :param upload_type: Optional (media, multipart, resumable)
        :return: The file
        """
        method_callable = lambda drive, **kwargs: drive.files.update(**kwargs)
        method_args = {
            "fileId": file_id,
            "uploadType": upload_type,
            "supportsAllDrives": True,
            "json": {"name": file_name},
        }
        return cast(
            FileModel,
            await execute_aiogoogle(
                method_callable=method_callable,
                service_account_credentials=self.service_account_credentials,
                api_name=self.api_name,
                api_version=self.api_version,
                **method_args,
            ),
        )

    async def move_file(
        self, file_id: str, parent_id: str, upload_type: str = "multipart"
    ) -> FileModel:
        """
        Changes parent of the file
        :param file_id: ID of the file to move
        :param parent_id: ID of the new parent
        :param upload_type: Optional (media, multipart, resumable)
        :return: The file
        """
        file = await self.get_file(file_id)
        method_callable = lambda drive, **kwargs: drive.files.update(**kwargs)

        method_args = {
            "fileId": file_id,
            "uploadType": upload_type,
            "supportsAllDrives": True,
            "addParents": parent_id,
            "removeParents": file["parents"][0],
        }
        return cast(
            FileModel,
            await execute_aiogoogle(
                method_callable=method_callable,
                service_account_credentials=self.service_account_credentials,
                api_name=self.api_name,
                api_version=self.api_version,
                **method_args,
            ),
        )


async def create_drive_class(service_file: json, subject: str) -> Drive:
    drive = Drive()
    await drive._async_init(service_file=service_file, subject=subject)
    return drive
