import json
from base64 import urlsafe_b64encode as base64_urlsafe_encode
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from mimetypes import guess_type as mimetypes_guess_type

from googleapi.Helpers.HelperFunctions import (
    build_service_account_credentials,
    execute_aiogoogle,
)
from googleapi.TypedDicts.Gmail import AttachmentsDictionary


class Gmail:
    """
    Implements the Gmail API to send mails
    """

    def __init__(
            self,
            mail_reply_address: str | None = None,
    ) -> None:
        """
        @param mail_reply_address: Address the replies to the mail will be sent to
        """
        self.mail_reply_address = mail_reply_address

        self.api_name = "gmail"
        self.api_version = "v1"

    async def _async_init(self, mail_sender: str, service_file: json):
        """
        @param mail_sender: Sender of the mail
        @param service_file: Service account credentials file
        """
        self.mail_sender = mail_sender
        self.service_account_credentials = await build_service_account_credentials(
            service_file=service_file,
            scopes=["https://www.googleapis.com/auth/gmail.send"],
            subject=mail_sender,
        )

    async def _build_message(
            self,
            mail_receiver: str,
            mail_subject: str,
            mail_content: str,
            attachments: list[AttachmentsDictionary] = None,
    ) -> dict:
        """
        Builds the body of the mail message
        @param mail_receiver: Receiver of the mail
        @param mail_subject: Subject of the mail
        @param mail_content: Content of the mail
        @param attachments: List of attachments
        @return: The body of the mail
        """
        # MIME stands for Multipurpose Internet Mail Extensions and is an internet standard that is used to support the transfer of single or multiple text
        # and non-text attachments
        message = MIMEMultipart()  # Create an empty MIMEMultipart message
        message["To"] = mail_receiver
        message["From"] = self.mail_sender
        message["Subject"] = mail_subject
        if self.mail_reply_address is not None:
            message["Reply-To"] = self.mail_reply_address
        mailContent = MIMEText(mail_content, "html")
        message.attach(mailContent)

        # Loop over the list of attachments
        for attachmentDictionary in attachments:
            if not isinstance(attachmentDictionary["attachment"], (str, bytes)):
                raise Exception("Attachment is not encoded as a string or bytes.")

            if isinstance(attachmentDictionary["attachment"], str):
                # Save the path, because this is needed later on
                attachmentPath = attachmentDictionary["attachment"]
                fileType, encoding = mimetypes_guess_type(
                    attachmentDictionary["filename"]
                )
                mainType, subType = fileType.split("/")
                attachmentData = MIMEBase(mainType, subType)

                # Open the attachment, read it and write its content into attachmentData
                with open(
                        attachmentPath, "rb"
                ) as file:  # "rb" = read, binary mode (e.g. images)
                    attachmentData.set_payload(file.read())
                # Add header to attachmentData so that the name of the attachment stays
                attachmentData.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=attachmentDictionary["filename"],
                )
                encode_base64(attachmentData)  # Encode the attachmentData
            else:
                attachmentData = MIMEBase(
                    attachmentDictionary["mime_maintype"],
                    attachmentDictionary["mime_subtype"],
                )
                attachmentData.set_payload(attachmentDictionary["attachment"])
                encode_base64(attachmentData)
                attachmentData.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=attachmentDictionary["filename"]
                             + "."
                             + attachmentDictionary["mime_subtype"],
                )
            message.attach(attachmentData)

        encoded_message = base64_urlsafe_encode(message.as_bytes()).decode()
        create_message = {"raw": encoded_message}
        return create_message

    async def send_message(
            self,
            mail_receivers: list[str],
            mail_subject: str,
            mail_content: str,
            attachments: list[AttachmentsDictionary] = None,
    ) -> None:
        """
        Sends the mail
        @param mail_receivers: List of receivers of the mail
        @param mail_subject: Subject of the mail
        @param mail_content: Content of the mail
        @param attachments: List of attachments
        @return: Nothing
        """
        if attachments is None:
            attachments = []

        method_callable = lambda gmail, **kwargs: gmail.users.messages.send(**kwargs)

        for mail_receiver in mail_receivers:
            message = await self._build_message(
                mail_receiver=mail_receiver,
                mail_subject=mail_subject,
                mail_content=mail_content,
                attachments=attachments,
            )
            method_args = {"userId": "me", "json": message}
            await execute_aiogoogle(
                method_callable=method_callable,
                service_account_credentials=self.service_account_credentials,
                api_name=self.api_name,
                api_version=self.api_version,
                **method_args,
            )


async def create_gmail_class(service_file: json, mail_sender: str, mail_reply_address: str | None = None) -> Gmail:
    gmail = Gmail(mail_reply_address=mail_reply_address)
    await gmail._async_init(service_file=service_file, mail_sender=mail_sender)
    return gmail
