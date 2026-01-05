from googleapi.Helpers.HelperFunctions import (
    build_service_account_credentials,
    execute_aiogoogle,
)
from googleapi.TypedDicts.Drive import DriveModel, DrivesModel, FileModel, FilesModel
from googleapi.TypedDicts.ServiceAccountFile import ServiceAccountFileModel


class Drive:
    """
    Implements the Google Drive API to manipulate Google Drive.
    """

    def __init__(self) -> None:
        self.api_name = "drive"
        self.api_version = "v3"
        self.service_account_credentials = None

    async def async_init(self, service_file: ServiceAccountFileModel, subject: str):
        """
        @param service_file: Service account credentials file
        @param subject: Subject who owns the drive
        """
        self.service_account_credentials = await build_service_account_credentials(
            service_file=service_file,
            scopes=["https://www.googleapis.com/auth/drive"],
            subject=subject,
        )

    async def get_drives(self) -> list[DriveModel]:
        """
        Gets the drives of the user
        @return: Drives of the user
        """
        method_callable = lambda drive, **kwargs: drive.drives.list()
        response: DrivesModel = await execute_aiogoogle(
            method_callable=method_callable,
            service_account_credentials=self.service_account_credentials,
            api_name=self.api_name,
            api_version=self.api_version,
        )
        return response.get("drives", [])

    async def get_drive(self, drive_id: str) -> DriveModel:
        """
        Gets the drive of the user
        @param drive_id: ID of the drive
        @return: Drive of the user
        """
        method_callable = lambda drive, **kwargs: drive.drives.get(**kwargs)
        method_args = {"driveId": drive_id}
        response: DriveModel = await execute_aiogoogle(
            method_callable=method_callable,
            service_account_credentials=self.service_account_credentials,
            api_name=self.api_name,
            api_version=self.api_version,
            **method_args,
        )
        return response

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
        response: FileModel = await execute_aiogoogle(
            method_callable=method_callable,
            service_account_credentials=self.service_account_credentials,
            api_name=self.api_name,
            api_version=self.api_version,
            **method_args,
        )
        return response

    async def get_files_from_parent(
        self,
        drive_id: str,
        parent_id: str = None,
        max_results: int = 50,
        include_trashed: bool = False,
        fields: str = None,
    ) -> list[FileModel]:
        """
        Gets all the files of the parent
        :param drive_id: ID of the parent drive
        :param parent_id: ID of the parent
        :param max_results: Max amount of results, standard 50
        :param include_trashed: Whether to include trashed items, standard False
        :param fields: Fields to return
        :return: List of the files
        """
        # If parent is not give, assume drive is the parent
        if parent_id is None:
            parent_id = drive_id

        # Need to do this since the API uses lowercase booleans
        if not include_trashed:
            search_query = f"parents in '{parent_id}' and trashed = false"
        else:
            search_query = f"parents in '{parent_id}'"

        method_callable = lambda drive, **kwargs: drive.files.list(**kwargs)

        method_args = {
            "corpora": "drive",
            "driveId": drive_id,
            "includeItemsFromAllDrives": True,
            "orderBy": "folder",
            "pageSize": max_results,
            "supportsAllDrives": True,
            "q": search_query,
        }

        if fields is not None:
            method_args["fields"] = fields

        response: FilesModel = await execute_aiogoogle(
            method_callable=method_callable,
            service_account_credentials=self.service_account_credentials,
            api_name=self.api_name,
            api_version=self.api_version,
            **method_args,
        )
        return response.get("files", [])

    async def download_file(self, file_id: str) -> bytes:
        """
        Downloads a file from the drive
        :param file_id: ID of the file to download
        :return: File as bytes
        """
        method_callable = lambda drive, **kwargs: drive.files.get(**kwargs)
        method_args = {"fileId": file_id, "alt": "media"}

        response: bytes = await execute_aiogoogle(
            method_callable=method_callable,
            service_account_credentials=self.service_account_credentials,
            api_name=self.api_name,
            api_version=self.api_version,
            **method_args,
        )
        return response

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

        response: FileModel = await execute_aiogoogle(
            method_callable=method_callable,
            service_account_credentials=self.service_account_credentials,
            api_name=self.api_name,
            api_version=self.api_version,
            **method_args,
        )
        return response

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
        response: FileModel = await execute_aiogoogle(
            method_callable=method_callable,
            service_account_credentials=self.service_account_credentials,
            api_name=self.api_name,
            api_version=self.api_version,
            **method_args,
        )
        return response

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
        response: FileModel = await execute_aiogoogle(
            method_callable=method_callable,
            service_account_credentials=self.service_account_credentials,
            api_name=self.api_name,
            api_version=self.api_version,
            **method_args,
        )
        return response


async def create_drive_class(
    service_file: ServiceAccountFileModel, subject: str
) -> Drive:
    drive = Drive()
    await drive.async_init(service_file=service_file, subject=subject)
    return drive
