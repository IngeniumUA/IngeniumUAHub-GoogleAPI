import json
from base64 import urlsafe_b64encode as base64_urlsafe_encode
from os import path as os_path
from random import choice as random_choice
from string import ascii_letters as string_ascii_letters
from string import digits as string_digits
from typing import List, cast

import aiogoogle.excs
from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import ServiceAccountCreds
from passlib.hash import sha256_crypt
from typing_extensions import Callable

from googleapi.TypedDicts.Directory import (
    UserModel,
    UserListModel,
    GroupModel,
    GroupListModel,
    MemberModel,
    MemberListModel,
    UserPhotoModel,
)


class Directory:
    """
    Implements the Google directory API to edit users and groups
    """

    def __init__(self, service_file_path: str, subject: str, domain: str):
        """
        @param service_file_path: Path to the service account credentials file
        @param subject: Subject who owns the directory
        """
        self.scopes = [
            "https://www.googleapis.com/auth/admin.directory.user",
            "https://www.googleapis.com/auth/admin.directory.group",
            "https://www.googleapis.com/auth/admin.directory.user.security",
        ]
        self.domain = domain
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
                directory = await google.discover(
                    api_name="directory", api_version="v3"
                )
                return await google.as_service_account(
                    method_callable(directory, **method_args)
                )
        except aiogoogle.excs.HTTPError as error:
            raise Exception(f"Aiogoogle error: {error}") from error

    async def get_users(self) -> List[UserModel]:
        """
        Returns all users of the directory
        @return: Returns all users
        """
        method_callable = lambda directory, **kwargs: directory.users.list(**kwargs)
        method_args = {"orderBy": "email", "domain": self.domain}
        return cast(
            UserListModel,
            await self._execute_aiogoogle(
                method_callable=method_callable, **method_args
            ),
        ).get("users", [])

    async def get_user(self, user_id: str) -> UserModel:
        """
        Gets the user of the directory
        @param user_id: User's primary email address, alias email address, or unique user ID.
        @return: The user
        """

        method_callable = lambda directory, **kwargs: directory.users.get(**kwargs)
        method_args = {
            "userKey": user_id,
            "viewType": "admin_view",
            "projection": "full",
        }
        return cast(
            UserModel,
            await self._execute_aiogoogle(
                method_callable=method_callable, **method_args
            ),
        )

    async def delete_user(self, user_id: str) -> None:
        """
        Deletes the user of the directory
        @param user_id: User's primary email address, alias email address, or unique user ID.
        @return: None
        """
        method_callable = lambda directory, **kwargs: directory.users.delete(**kwargs)
        method_args = {"userKey": user_id}
        await self._execute_aiogoogle(method_callable=method_callable, **method_args)

    async def create_user(
        self, email: str, password: str, first_name: str, last_name: str
    ) -> UserModel:
        """
        Creates a new user
        @param email: Email of the user
        @param password: Password of the user
        @param first_name: First name of the user
        @param last_name: Last name of the user
        @return: The created user
        """
        # Google only allows passwords between 8-100 in length
        if 100 < len(password) or len(password) < 8:
            raise Exception("Password needs to be between 8-100 characters")

        # Google accepts max 60 characters in first and last name
        if len(first_name) > 60:
            raise Exception("More then 60 characters in first name")

        if len(last_name) > 60:
            raise Exception("More then 60 characters in last name")

        # Check if the email domain is correct
        if email.split("@")[1] != "ingeniumua.be":
            raise Exception("Domain is not ingeniumua.be")

        characters = string_ascii_letters + string_digits
        salt = "".join(
            random_choice(characters) for _ in range(15)
        )  # Salt must be between 0-16 characters
        hashedPassword = sha256_crypt.hash(
            password, salt=salt, rounds=5000
        )  # Hash the password with the random salt, 5000 rounds because then they don't need to be specified in the hash format and Google only accepts it when not specified

        body = {
            "primaryEmail": email,
            "password": hashedPassword,
            "hashFunction": "crypt",
            "name": {"givenName": first_name, "familyName": last_name},
            "changePasswordAtNextLogin": False,
        }

        method_callable = lambda directory, **kwargs: directory.users.insert(**kwargs)
        method_args = {"body": body}
        return cast(
            UserModel,
            await self._execute_aiogoogle(
                method_callable=method_callable, **method_args
            ),
        )

    async def update_user(
        self, user_id: str, first_name: str = None, last_name: str = None
    ) -> UserModel:
        """
        Updates the user of the directory
        @param user_id: User's primary email address, alias email address, or unique user ID.
        @param first_name: Optional first name to be updated
        @param last_name: Optional last name to be updated
        @return: The updated user
        """
        # Check if at least one parameter is updated
        if all(x is None for x in [first_name, last_name]):
            raise Exception("Update arguments don't have a value")

        # Get the original user
        user = await self.get_user(user_id)
        currentFirstName = user["name"]["givenName"]
        currentLastName = user["name"]["familyName"]

        # If a parameter is not updated, assign the old one
        if first_name is None:
            first_name = currentFirstName
        if last_name is None:
            last_name = currentLastName

        # Check that it's not a needless update
        if first_name == currentFirstName and last_name == currentLastName:
            raise Exception("User already has these values")

        body = {"name": {"givenName": first_name, "familyName": last_name}}
        method_callable = lambda directory, **kwargs: directory.users.update(**kwargs)
        method_args = {"userKey": user_id, "body": body}
        return cast(
            UserModel,
            await self._execute_aiogoogle(
                method_callable=method_callable, method_args=method_args
            ),
        )

    async def update_user_password(self, password: str, user_id: str) -> UserModel:
        """
        Updates the password of the user of the directory
        @param password: New password
        @param user_id: User's primary email address, alias email address, or unique user ID.
        @return: The updated user
        """
        characters = string_ascii_letters + string_digits
        salt = "".join(
            random_choice(characters) for _ in range(15)
        )  # Salt must be between 0-16 characters
        # Hash the password with the random salt, 5000 rounds because then they don't need to be specified in the hash
        # format and Google only accepts it when not specified
        hashedPassword = sha256_crypt.hash(password, salt=salt, rounds=5000)

        body = {
            "password": hashedPassword,
            "hashFunction": "crypt",
            "changePasswordAtNextLogin": False,
        }

        method_callable = lambda directory, **kwargs: directory.users.update(**kwargs)
        method_kwargs = {"userKey": user_id, "body": body}
        return cast(
            UserModel,
            await self._execute_aiogoogle(
                method_callable=method_callable, **method_kwargs
            ),
        )

    async def update_user_photo(self, user_id: int, photo_path: str) -> UserPhotoModel:
        """
        Updates the photo of the user of the directory
        @param user_id: User's primary email address, alias email address, or unique user ID.
        @param photo_path: The path or url to the photo
        @return: User photo
        """
        if os_path.getsize(photo_path) >= 10**7:
            raise Exception("File size is max 10Mb")

        photoName = os_path.basename(photo_path)
        fileType = photoName.split(".")[1]

        if fileType not in ["jpeg", "png", "gif", "bmp", "tiff"]:
            raise Exception("Filetype not supported")

        with open(photo_path, "rb") as f:  # "rb" = read, binary mode (e.g. images)
            photoData = f.read()
        photoDataBase64 = base64_urlsafe_encode(photoData).decode("utf-8")

        body = {"photoData": photoDataBase64, "mimeType": fileType}

        method_callable = lambda directory, **kwargs: directory.users.photos.update(
            **kwargs
        )
        method_args = {"userKey": user_id, "body": body}
        return cast(
            UserPhotoModel,
            await self._execute_aiogoogle(
                method_callable=method_callable, **method_args
            ),
        )

    async def get_user_photo(self, user_id: int) -> UserPhotoModel:
        """
        Gets the photo of the user of the directory
        @param user_id: User's primary email address, alias email address, or unique user ID.
        @return: User Photo
        """
        method_callable = lambda directory, **kwargs: directory.users.photos.get(
            **kwargs
        )
        method_args = {"userKey": user_id}
        return cast(
            UserPhotoModel,
            await self._execute_aiogoogle(
                method_callable=method_callable, **method_args
            ),
        )

    async def delete_user_photo(self, user_id: int) -> None:
        """
        Deletes the photo of the user of the directory
        @param user_id: User's primary email address, alias email address, or unique user ID.
        @return: Nothing
        """
        method_callable = lambda directory, **kwargs: directory.users.photos.delete(
            **kwargs
        )
        method_args = {"userKey": user_id}
        await self._execute_aiogoogle(method_callable=method_callable, **method_args)

    async def get_groups(self) -> List[GroupModel]:
        """
        Returns the groups of the directory
        @return: All the groups
        """
        method_callable = lambda directory, **kwargs: directory.groups.list(**kwargs)
        method_args = {"domain": self.domain, "orderBy": "email"}
        return cast(
            GroupListModel,
            await self._execute_aiogoogle(
                method_callable=method_callable, **method_args
            ),
        ).get("groups", [])

    async def get_group(self, group_id: str) -> GroupModel:
        """
        Gets the group of the directory
        @param group_id: Group's email address, group alias, or the unique group ID.
        @return: The group
        """
        method_callable = lambda directory, **kwargs: directory.groups.get(**kwargs)
        method_args = {"groupKey": group_id}
        return cast(
            GroupModel,
            await self._execute_aiogoogle(
                method_callable=method_callable, **method_args
            ),
        )

    async def delete_group(self, group_id: str) -> None:
        """
        Deletes the group of the directory
        @param group_id: Group's email address, group alias, or the unique group ID.
        @return: Nothing
        """
        method_callable = lambda directory, **kwargs: directory.groups.delete(**kwargs)
        method_args = {
            "groupKey": group_id,
        }
        await self._execute_aiogoogle(method_callable=method_callable, **method_args)

    async def create_group(
        self, email: str, name: str, description: str = None
    ) -> GroupModel:
        """
        Creates the group in the directory
        @param email: Email of the group
        @param name: Name of the group
        @param description: Optional description of the group
        @return: The created group
        """
        # Check if the email domain is correct
        if email.split("@")[1] != "ingeniumua.be":
            raise Exception("Domain is not ingeniumua.be")

        body = {"email": email, "name": name, "description": description}
        method_callable = lambda directory, **kwargs: directory.groups.insert(**kwargs)
        method_args = {"body": body}
        return cast(
            GroupModel,
            await self._execute_aiogoogle(
                method_callable=method_callable, **method_args
            ),
        )

    async def update_group(
        self,
        group_id: str,
        email: str = None,
        name: str = None,
        description: str = None,
    ) -> GroupModel:
        """
        Updates the group in the directory
        @param group_id: Group's email address, group alias, or the unique group ID.
        @param email: Email of the group
        @param name: Optional name of the group
        @param description: Optional description of the group
        @return: The updated group
        """
        # Check if at least one parameter is updated
        if all(x is None for x in [email, name, description]):
            raise Exception("Update arguments don't have a value")

        # Get the original user
        group = await self.get_group(group_id)
        currentEmail = group["email"]
        currentName = group["name"]
        currentDescription = group["description"]

        # If a parameter is not updated, assign the old one
        if email is None:
            email = currentEmail
        # Check if the email domain is correct
        elif email.split("@")[1] != "ingeniumua.be":
            raise Exception("Domain is not ingeniumua.be")
        if name is None:
            name = currentName
        if description is None:
            description = currentDescription

        # Check that it's not a needless update
        if (
            email == currentEmail
            and name == currentName
            and description == currentDescription
        ):
            raise Exception("User already has these values")

        body = {"email": email, "name": name, "description": description}

        method_callable = lambda directory, **kwargs: directory.groups.update(**kwargs)
        method_args = {"groupKey": group_id, "body": body}
        return cast(
            GroupModel,
            await self._execute_aiogoogle(
                method_callable=method_callable, **method_args
            ),
        )

    async def get_group_members(self, group_id: str) -> List[MemberModel]:
        """
        Gets all the members of the group
        @param group_id: Group's email address, group alias, or the unique group ID.
        @return: The members of the group
        """

        method_callable = lambda directory, **kwargs: directory.members.list(**kwargs)
        method_args = {"groupKey": group_id}
        return cast(
            MemberListModel,
            await self._execute_aiogoogle(
                method_callable=method_callable, **method_args
            ),
        ).get("members", [])

    async def add_group_member(self, user_id: str, group_id: str) -> MemberModel:
        """
        Adds the user to the group
        @param user_id: User's primary email address, alias email address, or unique user ID.
        @param group_id: Group's email address, group alias, or the unique group ID.
        @return: The added member
        """
        user = await self.get_user(user_id)
        method_callable = lambda directory, **kwargs: directory.members.insert(**kwargs)
        method_args = {"groupKey": group_id, "body": user}
        return cast(
            MemberModel,
            await self._execute_aiogoogle(
                method_callable=method_callable, **method_args
            ),
        )

    async def delete_group_member(self, user_id: int, group_id: str) -> None:
        """
        Deletes the member from the group
        @param user_id: User's primary email address, alias email address, or unique user ID.
        @param group_id: Group's email address, group alias, or the unique group ID.
        @return: Nothing
        """
        method_callable = lambda directory, **kwargs: directory.members.delete(**kwargs)
        method_args = {"groupKey": group_id, "memberKey": user_id}
        await self._execute_aiogoogle(method_callable=method_callable, **method_args)

    async def remove_all_sessions(self) -> None:
        """
        Logs all the users out of all sessions.
        @return: Nothing
        """
        users = await self.get_users()
        method_callable = lambda directory, **kwargs: directory.users.signOut(**kwargs)
        for user in users:
            method_args = {"userKey": user.get("id")}
            await self._execute_aiogoogle(
                method_callable=method_callable, **method_args
            )
