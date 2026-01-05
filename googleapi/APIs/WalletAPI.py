import datetime

from google.auth import crypt, jwt
from starlette.exceptions import HTTPException

from googleapi.Helpers.HelperFunctions import (
    build_service_account_credentials,
    execute_aiogoogle,
)
from googleapi.TypedDicts.ServiceAccountFile import ServiceAccountFileModel
from googleapi.TypedDicts.Wallet import EventClassModel, EventObjectModel


class Wallet:
    def __init__(self) -> None:
        self.api_name = "walletobjects"
        self.api_version = "v1"
        self.scopes = ["https://www.googleapis.com/auth/wallet_object.issuer"]
        self.issuer_id = None
        self.service_account_credentials = None

    async def async_init(
        self,
        service_file: ServiceAccountFileModel,
        issuer_id: int,
    ):
        """
        @param service_file: Service account credentials file
        """
        self.service_account_credentials = await build_service_account_credentials(
            service_file=service_file, scopes=self.scopes, subject=""
        )
        self.issuer_id = issuer_id

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

    async def create_class(self, new_class: EventClassModel) -> dict:
        method_callable = lambda wallet, **kwargs: wallet.eventticketclass.insert(
            **kwargs
        )
        method_args = {"json": new_class}

        try:
            # Try to create class
            response = await execute_aiogoogle(
                method_callable=method_callable,
                service_account_credentials=self.service_account_credentials,
                api_name=self.api_name,
                api_version=self.api_version,
                use_new_version = True,
                **method_args,
            )
            return response

        except HTTPException as error:
            # If class already exists, get it
            if error.status_code == 409:
                method_callable = lambda wallet, **kwargs: wallet.eventticketclass.get(
                    **kwargs
                )
                method_args = {"resourceId": new_class.get("id")}
                response = await execute_aiogoogle(
                    method_callable=method_callable,
                    service_account_credentials=self.service_account_credentials,
                    api_name=self.api_name,
                    api_version=self.api_version,
                    use_new_version=True,
                    **method_args,
                )
                return response
            raise

    async def create_object(
        self,
        new_object: EventObjectModel,
    ) -> dict:
        method_callable = lambda wallet, **kwargs: wallet.eventticketobject.insert(
            **kwargs
        )
        method_args = {"json": new_object}

        try:
            response = await execute_aiogoogle(
                method_callable=method_callable,
                service_account_credentials=self.service_account_credentials,
                api_name=self.api_name,
                api_version=self.api_version,
                use_new_version=True,
                **method_args,
            )

            return response
        except HTTPException as error:
            # If object already exists, get it
            if error.status_code == 409:
                method_callable = lambda wallet, **kwargs: wallet.eventticketobject.get(
                    **kwargs
                )
                method_args = {"resourceId": new_object.get("id")}
                response = await execute_aiogoogle(
                    method_callable=method_callable,
                    service_account_credentials=self.service_account_credentials,
                    api_name=self.api_name,
                    api_version=self.api_version,
                    use_new_version=True,
                    **method_args,
                )
                return response
            raise

    async def create_link(
        self,
        new_class: EventClassModel,
        new_object: EventObjectModel,
    ) -> str:
        link_class = await self.create_class(new_class=new_class)

        link_object = await self.create_object(new_object=new_object)

        # Create the JWT claims
        claims = {
            "iss": self.service_account_credentials.client_email,
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


async def create_wallet_class(
    service_file: ServiceAccountFileModel, issuer_id: int
) -> Wallet:
    wallet = Wallet()
    await wallet.async_init(
        service_file,
        issuer_id,
    )
    return wallet
