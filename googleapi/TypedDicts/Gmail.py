from typing import TypedDict


class AttachmentsDictionary(TypedDict):
    """
    A dictionary that stores all the attachments, also used for type hinting.
    MIME types: https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types

    :param attachment: The attachment data as bytes or the path as a string
    :param filename: The desired name of the attachment file
    :param mime_maintype: The MIME main type
    :param mime_subtype: The MIME subtype
    """
    attachment: str | bytes
    filename: str
    mime_maintype: str | None
    mime_subtype: str | None
