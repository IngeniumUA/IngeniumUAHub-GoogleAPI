from base64 import urlsafe_b64encode as base64_urlsafe_encode
from string import ascii_letters as string_ascii_letters
from string import digits as string_digits
from googleapiclient.errors import HttpError as GoogleHttpError
from random import choice as random_choice
from os import path as os_path
from passlib.hash import sha256_crypt
from google.oauth2 import service_account
from googleapiclient.discovery import build


class WorkspaceClass:
    """
    Implements the Google Workspace API to edit users and groups
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
        self.subject = "workspace@ingeniumua.be"

        if not os_path.exists(service_file_path):
            raise Exception("Service account json path does not exist")

        self.serviceFilePath = service_file_path
        self.service = self._build_service()

    def _build_service(self):
        # Create credentials from the service account file
        credentials = service_account.Credentials.from_service_account_file(
            filename=self.serviceFilePath, scopes=self.scopes, subject=self.subject
        )
        # Build the service
        service = build("admin", "directory_v1", credentials=credentials)
        return service

    def get_users(self) -> list[dict]:
        """
        :return: Returns a list of dictionaries of all users
        """
        usersList = (
            self.service.users()
            .list(domain=self.domain, orderBy="email")
            .execute()
            .get("users", [])
        )
        return usersList

    def get_user(self, user_id: str) -> dict:
        """
        :param user_id: Id of the user
        :return: Returns a dictionary of the user
        """
        try:
            user = (
                self.service.users()
                .get(userKey=user_id, viewType="admin_view", projection="full")
                .execute()
            )
            return user
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def delete_user(self, user_id: str):
        """
        :param user_id: The id of the user
        :return: Nothing
        """
        try:
            self.service.users().delete(userKey=user_id).execute()
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def create_user(self, email: str, password: str, first_name: str, last_name: str):
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
            self.service.users().insert(body=body).execute()
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def update_user(self, user_id: str, first_name: str = None, last_name: str = None):
        """
        :param user_id: Id of the user
        :param first_name: Optional first name to be updated
        :param last_name: Optional last name to be updated
        :return: Nothing
        """
        # Check if at least one parameter is updated
        if all(x is None for x in [first_name, last_name]):
            raise Exception("Update arguments don't have a value")

        # Get the original user
        user = self.get_user(user_id)
        currentFirstName = user["name"]["givenName"]
        currentLastName = user["name"]["familyName"]

        # If a parameter is not updated, assign the old one
        if first_name is None:
            first_name = currentFirstName
        if last_name is None:
            last_name = currentLastName

        # Check that its not a needless update
        if first_name == currentFirstName and last_name == currentLastName:
            raise Exception("User already has these values")

        body = {"name": {"givenName": first_name, "familyName": last_name}}

        try:
            self.service.users().update(body=body, userKey=user_id).execute()
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def update_user_password(self, password: str, user_id: int):
        """
        :param user_id: Id of the user
        :param password: New password
        :return: Nothing
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

        try:
            self.service.users().update(body=body, userKey=user_id).execute()
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def update_user_photo(self, user_id: int, photo_path: str):
        """
        :param user_id: Id of the user
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
            self.service.users().photos().update(body=body, userKey=user_id).execute()
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def get_user_photo(self, user_id: int):
        try:
            photo = self.service.users().photos().get(userKey=user_id).execute()
            return photo
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def delete_user_photo(self, user_id: int):
        try:
            self.service.users().photos().delete(userKey=user_id).execute()
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def get_groups(self) -> list[dict]:
        """
        :return: Returns a list of dictionaries of all groups
        """
        try:
            groupsList = (
                self.service.groups()
                .list(domain=self.domain, orderBy="email")
                .execute()
                .get("groups", [])
            )
            return groupsList
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def get_group(self, group_id: str) -> dict:
        """
        :param group_id: Id of the group
        :return: Returns a dictionary of the user
        """
        try:
            group = self.service.groups().get(groupKey=group_id).execute()
            return group
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def delete_group(self, group_id: str):
        """
        :param group_id: Id of the group
        :return: Nothing
        """
        try:
            group = self.service.groups().delete(groupKey=group_id).execute()
            return group
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def create_group(self, email: str, name: str, description: str = None):
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
            self.service.groups().insert(body=body).execute()
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def update_group(
            self,
            group_id: str,
            email: str = None,
            name: str = None,
            description: str = None,
    ):
        # Check if at least one parameter is updated
        if all(x is None for x in [email, name, description]):
            raise Exception("Update arguments don't have a value")

        # Get the original user
        group = self.get_group(group_id)
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

        # Check that its not a needless update
        if (
                email == currentEmail
                and name == currentName
                and description == currentDescription
        ):
            raise Exception("User already has these values")

        body = {"email": email, "name": name, "description": description}

        try:
            self.service.groups().update(groupKey=group_id, body=body).execute()
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def get_group_members(self, group_id: str) -> list[dict]:
        """
        :param group_id: Id of the group
        :return: Returns a list of dictionaries of all members
        """
        try:
            members = (
                self.service.members()
                .list(groupKey=group_id)
                .execute()
                .get("members", [])
            )
            return members
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def add_group_member(self, user_id: str, group_id: str):
        """
        :param user_id: Id of the user
        :param group_id: Id of the group
        :return: Nothing
        """
        user = self.get_user(user_id)
        try:
            self.service.members().insert(groupKey=group_id, body=user).execute()
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def delete_group_member(self, user_id: int, group_id: str):
        """
        :param user_id: Id of the user
        :param group_id: Id of the group
        :return: Nothing
        """
        try:
            self.service.members().delete(
                groupKey=group_id, memberKey=user_id
            ).execute()
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def remove_all_sessions(self) -> None:
        """
        Logs all the users out of all sessions. To be used when starting a new year and changing account holders.

        :return: Nothing
        """
        users = self.get_users()
        for user in users:
            self.service.users().signOut(userKey=user["id"]).execute()