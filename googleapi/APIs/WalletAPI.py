import datetime
import json

from google.auth import crypt, jwt

from googleapi.Helpers.HelperFunctions import (
    build_service_account_credentials,
    execute_aiogoogle,
)
from googleapi.TypedDicts.Wallet import EventClassModel, EventObjectModel


class Wallet:
    def __init__(self) -> None:
        self.api_name = "walletobjects"
        self.api_version = "v1"
        self.scopes = ["https://www.googleapis.com/auth/wallet_object.issuer"]

    async def _async_init(
        self,
        service_file: json,
        issuer_id: int,
        base_url: str,
        class_url: str,
        object_url: str,
    ):
        """
        @param service_file: Service account credentials file
        """
        self.service_account_credentials = await build_service_account_credentials(
            service_file=service_file, scopes=self.scopes, subject=""
        )
        self.issuer_id = issuer_id
        self.base_url = base_url
        self.class_url = class_url
        self.object_url = object_url

    async def create_class_body(
        self,
        class_suffix: str,
        event_name: str,
        issuer_name: str,
        logo_url: str,
        content_description: str,
        event_date: datetime.datetime,
        location_name: str,
    ) -> EventClassModel:
        class_id = f"{self.issuer_id}.{class_suffix}"

        class_body: EventClassModel = {
            "id": class_id,
            "eventName": {"defaultValue": {"language": "nl-BE", "value": event_name}},
            "issuerName": issuer_name,
            "reviewStatus": "underReview",
            "logo": {
                "sourceUri": {"uri": logo_url},
                "contentDescription": {
                    "defaultValue": {"language": "nl-BE", "value": content_description}
                },
            },
            "dateTime": {"start": str(event_date).replace(" ", "T").split("+")[0]},
            "venue": {
                "name": {"defaultValue": {"language": "nl-BE", "value": location_name}},
                "address": {
                    "defaultValue": {"language": "nl-BE", "value": location_name}
                },
            },
        }
        return class_body

    async def create_object_body(
        self,
        object_suffix: str,
        class_suffix: str,
        banner_link: str,
        content_description: str,
        qr_code: str,
        background_color: str,
        end_date: datetime.datetime,
        number: int,
    ) -> EventObjectModel:
        class_id = f"{self.issuer_id}.{class_suffix}"
        object_id = f"{self.issuer_id}.{object_suffix}"

        object_body: EventObjectModel = {
            "id": object_id,
            "classId": class_id,
            "state": "ACTIVE",
            "heroImage": {
                "sourceUri": {"uri": banner_link},
                "contentDescription": {
                    "defaultValue": {
                        "language": "nl-BE",
                        "value": content_description,
                    }
                },
            },
            "barcode": {"type": "QR_CODE", "value": qr_code},
            "hexBackgroundColor": background_color,
            "validTimeInterval": {
                "start": {
                    "date": str(datetime.datetime.now()).replace(" ", "T").split("+")[0]
                },
                "end": {"date": str(end_date).replace(" ", "T").split("+")[0]},
            },
            "ticketNumber": str(number),
        }
        return object_body

    async def create_class(
        self, event_name: str, event_date: datetime.datetime, new_class: EventClassModel
    ) -> dict:
        class_suffix = event_name.replace(" ", "_") + "_" + str(event_date.year)
        class_id = f"{self.issuer_id}.{class_suffix}"

        # Check if class exists
        method_callable = lambda wallet, **kwargs: wallet.eventticketclass.get(**kwargs)
        method_args = {"resourceId": class_id}
        response = await execute_aiogoogle(
            method_callable=method_callable,
            service_account_credentials=self.service_account_credentials,
            api_name=self.api_name,
            api_version=self.api_version,
            **method_args,
        )

        if response != 404:
            return response

        method_callable = lambda wallet, **kwargs: wallet.eventticketclass.insert(
            **kwargs
        )

        method_args = {"json": new_class}
        response = await execute_aiogoogle(
            method_callable=method_callable,
            service_account_credentials=self.service_account_credentials,
            api_name=self.api_name,
            api_version=self.api_version,
            **method_args,
        )
        return response

    async def create_object(
        self,
        event_name: str,
        object_suffix: str,
        event_date: datetime.datetime,
        new_object: EventObjectModel,
    ) -> dict:
        object_id = f"{self.issuer_id}.{object_suffix}"

        # Check if object exists
        method_callable = lambda wallet, **kwargs: wallet.eventticketobject.get(
            **kwargs
        )
        method_args = {"resourceId": object_id}
        response = await execute_aiogoogle(
            method_callable=method_callable,
            service_account_credentials=self.service_account_credentials,
            api_name=self.api_name,
            api_version=self.api_version,
            **method_args,
        )

        if response != 404:
            return response

        method_callable = lambda wallet, **kwargs: wallet.eventticketobject.insert(
            **kwargs
        )

        method_args = {"json": new_object}
        response = await execute_aiogoogle(
            method_callable=method_callable,
            service_account_credentials=self.service_account_credentials,
            api_name=self.api_name,
            api_version=self.api_version,
            **method_args,
        )

        return response

    async def create_link(
        self,
        qr_code: str,
        event_name: str,
        event_date: datetime.datetime,
        new_class: EventClassModel,
        new_object: EventObjectModel,
    ) -> str:
        link_class = await self.create_class(
            event_name=event_name, event_date=event_date, new_class=new_class
        )

        link_object = await self.create_object(
            event_name=event_name,
            object_suffix=qr_code,
            event_date=event_date,
            new_object=new_object,
        )

        # Create the JWT claims
        claims = {
            "iss": self.service_account_credentials.service_account_email,
            "aud": "google",
            "origins": ["www.ingeniumua.be"],
            "typ": "savetowallet",
            "payload": {
                # The listed classes and objects will be created
                "eventTicketClasses": [link_class],
                "eventTicketObjects": [link_object],
            },
        }

        # The service account credentials are used to sign the JWT
        signer = crypt.RSASigner.from_service_account_info(
            self.service_account_credentials
        )
        token = jwt.encode(signer, claims).decode("utf-8")

        return f"https://pay.google.com/gp/v/save/{token}"


async def create_google_wallet_class(
    service_file: json, issuer_id: int, base_url: str, class_name: str, object_name: str
) -> Wallet:
    wallet = Wallet()
    await wallet._async_init(
        service_file,
        issuer_id,
        base_url,
        f"{base_url}/{class_name}",
        f"{base_url}/objects/{object_name}",
    )
    return wallet
