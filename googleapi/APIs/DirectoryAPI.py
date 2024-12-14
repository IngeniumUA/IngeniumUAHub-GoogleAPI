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

from googleapi.TypedDicts.Directory import UserModel, UserListModel, GroupModel, GroupListModel, MemberModel, \
    MemberListModel


class Directory:
    """
    Implements the Google directory API to edit users and groups
    """

    def __init__(self, service_file_path: str):
        """
        :param service_file_path: The path to the service account credentials file
        """
        self.scopes = [
            "https://www.googleapis.com/auth/admin.directory.user",
            "https://www.googleapis.com/auth/admin.directory.group",
            "https://www.googleapis.com/auth/admin.directory.user.security",
        ]
        self.domain = "ingeniumua.be"
        self.subject = "directory@ingeniumua.be"

        if not os_path.exists(service_file_path):
            raise Exception("Service account json path does not exist")

        self.serviceFilePath = service_file_path
        self.service_account_credentials = self._build_service_account_credentials()

    def _build_service_account_credentials(self):
        service_account_key = json.load(open(self.serviceFilePath))
        credentials = ServiceAccountCreds(scopes=self.scopes, **service_account_key, subject=self.subject)
        return credentials

    async def get_users(self) -> List[UserModel]:
        """
        :return: Returns a list of dictionaries of all users
        """
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                directory = await google.discover("admin", "directory_v1")
                return cast(UserListModel, await google.as_service_account(directory.users.list(domain=self.domain, orderBy="email"))).get('users', [])
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def get_user(self, user_id: str) -> UserModel:
        """
        :param user_id: User's primary email address, alias email address, or unique user ID.
        :return: Returns a dictionary of the user
        """
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                directory = await google.discover("admin", "directory_v1")
                return cast(UserModel, await google.as_service_account(directory.users.get(userKey=user_id, viewType="admin_view", projection="full")))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def delete_user(self, user_id: str):
        """
        :param user_id: User's primary email address, alias email address, or unique user ID.
        :return: Nothing
        """
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                directory = await google.discover("admin", "directory_v1")
                await google.as_service_account(directory.users.delete(userKey=user_id))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def create_user(self, email: str, password: str, first_name: str, last_name: str):
        """
        :param email: Email of the user
        :param password: Password of the user
        :param first_name: First name of the user
        :param last_name: Last name of the user
        :return: Nothing
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

        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                directory = await google.discover("admin", "directory_v1")
                await google.as_service_account(directory.users.insert(body=body))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def update_user(self, user_id: str, first_name: str = None, last_name: str = None):
        """
        :param user_id: User's primary email address, alias email address, or unique user ID.
        :param first_name: Optional first name to be updated
        :param last_name: Optional last name to be updated
        :return: Nothing
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

        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                directory = await google.discover("admin", "directory_v1")
                await google.as_service_account(directory.users.update(body=body, userKey=user_id))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def update_user_password(self, password: str, user_id: int):
        """
        :param user_id: User's primary email address, alias email address, or unique user ID.
        :param password: New password
        :return: Nothing
        """
        characters = string_ascii_letters + string_digits
        salt = "".join(random_choice(characters) for _ in range(15))  # Salt must be between 0-16 characters
        # Hash the password with the random salt, 5000 rounds because then they don't need to be specified in the hash
        # format and Google only accepts it when not specified
        hashedPassword = sha256_crypt.hash(password, salt=salt, rounds=5000)

        body = {
            "password": hashedPassword,
            "hashFunction": "crypt",
            "changePasswordAtNextLogin": False,
        }

        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                directory = await google.discover("admin", "directory_v1")
                await google.as_service_account(directory.users.update(body=body, userKey=user_id))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def update_user_photo(self, user_id: int, photo_path: str):
        """
        :param user_id: User's primary email address, alias email address, or unique user ID.
        :param photo_path: The path or url of the photo
        :return: Nothing
        """
        if os_path.getsize(photo_path) >= 10 ** 7:
            raise Exception("File size is max 10Mb")

        photoName = os_path.basename(photo_path)
        fileType = photoName.split(".")[1]

        if fileType not in ["jpeg", "png", "gif", "bmp", "tiff"]:
            raise Exception("Filetype not supported")

        with open(photo_path, "rb") as f:  # "rb" = read, binary mode (e.g. images)
            photoData = f.read()
        photoDataBase64 = base64_urlsafe_encode(photoData).decode("utf-8")

        body = {"photoData": photoDataBase64, "mimeType": fileType}
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                directory = await google.discover("admin", "directory_v1")
                await google.as_service_account(directory.users.photos.update(body=body, userKey=user_id))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def get_user_photo(self, user_id: int):
        """
        :param user_id: User's primary email address, alias email address, or unique user ID.
        :return: Nothing
        """
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                directory = await google.discover("admin", "directory_v1")
                photo = await google.as_service_account(directory.users.photos.get(userKey=user_id))
                return photo
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def delete_user_photo(self, user_id: int):
        """
        :param user_id: User's primary email address, alias email address, or unique user ID.
        :return: Nothing
        """
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                directory = await google.discover("admin", "directory_v1")
                await google.as_service_account(directory.users.photos.delete(userKey=user_id))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def get_groups(self) -> List[GroupModel]:
        """
        :return: Returns a list of dictionaries of all groups
        """
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                directory = await google.discover("admin", "directory_v1")
                return cast(GroupListModel, await google.as_service_account(directory.groups.list(domain=self.domain, orderBy="email"))).get("groups", [])
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def get_group(self, group_id: str) -> GroupModel:
        """
        :param group_id: Group's email address, group alias, or the unique group ID.
        :return: Returns a dictionary of the user
        """
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                directory = await google.discover("admin", "directory_v1")
                return cast(GroupModel, await google.as_service_account(directory.groups.get(groupKey=group_id)))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def delete_group(self, group_id: str):
        """
        :param group_id: Group's email address, group alias, or the unique group ID.
        :return: Nothing
        """
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                directory = await google.discover("admin", "directory_v1")
                await google.as_service_account(directory.groups.delete(groupKey=group_id))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def create_group(self, email: str, name: str, description: str = None):
        """
        :param email: Email of the group
        :param name: Name of the group
        :param description: Description of the group, optional
        :return: Nothing
        """

        # Check if the email domain is correct
        if email.split("@")[1] != "ingeniumua.be":
            raise Exception("Domain is not ingeniumua.be")

        body = {"email": email, "name": name, "description": description}

        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                directory = await google.discover("admin", "directory_v1")
                await google.as_service_account(directory.groups.insert(body=body))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def update_group(self, group_id: str, email: str = None, name: str = None, description: str = None,):
        """
        :param group_id: Group's email address, group alias, or the unique group ID.
        :param email: Email of the group
        :param name: Name of the group, optional
        :param description: Description of the group, optional
        :return: Nothing
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

        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                directory = await google.discover("admin", "directory_v1")
                await google.as_service_account(directory.groups.update(groupKey=group_id, body=body))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def get_group_members(self, group_id: str) -> List[MemberModel]:
        """
        :param group_id: Group's email address, group alias, or the unique group ID.
        :return: Returns a list of dictionaries of all members
        """
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                directory = await google.discover("admin", "directory_v1")
                return cast(MemberListModel, await google.as_service_account(directory.members.list(groupKey=group_id))).get("members", [])
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def add_group_member(self, user_id: str, group_id: str):
        """
        :param user_id: User's primary email address, alias email address, or unique user ID.
        :param group_id: Group's email address, group alias, or the unique group ID.
        :return: Nothing
        """
        user = await self.get_user(user_id)
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                directory = await google.discover("admin", "directory_v1")
                await google.as_service_account(directory.members.insert(groupKey=group_id, body=user))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def delete_group_member(self, user_id: int, group_id: str):
        """
        :param user_id: User's primary email address, alias email address, or unique user ID.
        :param group_id: Group's email address, group alias, or the unique group ID.
        :return: Nothing
        """
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                directory = await google.discover("admin", "directory_v1")
                await google.as_service_account(directory.members.delete(groupKey=group_id, memberKey=user_id))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def remove_all_sessions(self) -> None:
        """
        Logs all the users out of all sessions. To be used when starting a new year and changing account holders.
        :return: Nothing
        """
        users = await self.get_users()
        for user in users:
            try:
                async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                    directory = await google.discover("admin", "directory_v1")
                    await google.as_service_account(directory.users.signOut(userKey=user["id"]))
            except aiogoogle.excs.HTTPError as error:
                raise Exception("Aiogoogle error") from error
