import datetime
import json

from google.auth import crypt, jwt

from googleapi.Helpers.HelperFunctions import (
    build_service_account_credentials,
    execute_aiogoogle,
)


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

    async def create_class(
        self, event_name: str, event_date: datetime.datetime, locatie_naam: str
    ) -> dict:
        class_suffix = event_name.replace(" ", "_") + "_" + str(event_date.year)
        class_id = f"{self.issuer_id}.{class_suffix}"
        class_url = f"{self.class_url}/{self.issuer_id}.{class_suffix}"

        # Check if class exists
        method_callable = lambda wallet, **kwargs: wallet.genericclass().get(**kwargs)
        method_args = {"resourceId": class_url}
        response = await execute_aiogoogle(
            method_callable=method_callable,
            service_account_credentials=self.service_account_credentials,
            api_name=self.api_name,
            api_version=self.api_version,
            **method_args,
        )

        if response.status == 200:
            return response.json()
        elif response.status != 404:
            return response.json()

        new_class = {
            "id": class_id,
            "eventName": {"defaultValue": {"language": "nl-BE", "value": event_name}},
            "issuerName": "Ingenium UA",
            "reviewStatus": "underReview",
            "logo": {
                "sourceUri": {
                    "uri": "https://www.ingeniumua.be/assets/Ingenium-schild.png"
                },
                "contentDescription": {
                    "defaultValue": {"language": "nl-BE", "value": "Logo van Ingenium"}
                },
            },
            "dateTime": {"start": str(event_date).replace(" ", "T").split("+")[0]},
            "venue": {
                "name": {"defaultValue": {"language": "nl-BE", "value": locatie_naam}},
                "address": {
                    "defaultValue": {"language": "nl-BE", "value": locatie_naam}
                },
            },
        }

        method_callable = lambda wallet, **kwargs: wallet.genericclass().insert(
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
        return response.json()

    async def create_object(
        self,
        event_name: str,
        object_suffix: str,
        qr_code,
        banner_link: str,
        end_date: datetime.datetime,
        number: int,
        event_date: datetime.datetime,
    ) -> dict:
        class_suffix = event_name.replace(" ", "_") + "_" + str(event_date.year)
        object_id = f"{self.issuer_id}.{object_suffix}"
        object_url = f"{self.object_url}/{self.issuer_id}.{object_suffix}"
        class_id = f"{self.issuer_id}.{class_suffix}"

        # Check if object exists
        method_callable = lambda wallet, **kwargs: wallet.genericobject().get(**kwargs)
        method_args = {"resourceId": object_url}
        response = await execute_aiogoogle(
            method_callable=method_callable,
            service_account_credentials=self.service_account_credentials,
            api_name=self.api_name,
            api_version=self.api_version,
            **method_args,
        )

        if response.status == 200:
            return response.json()
        elif response.status != 404:
            return response.json()

        new_object = {
            "id": object_id,
            "classId": class_id,
            "state": "ACTIVE",
            "heroImage": {
                "sourceUri": {"uri": banner_link},
                "contentDescription": {
                    "defaultValue": {
                        "language": "nl-BE",
                        "value": "Banner van het event",
                    }
                },
            },
            "barcode": {"type": "QR_CODE", "value": qr_code},
            "hexBackgroundColor": "#1F2980",
            "validTimeInterval": {
                "start": {
                    "date": str(datetime.datetime.now()).replace(" ", "T").split("+")[0]
                },
                "end": {"date": str(end_date).replace(" ", "T").split("+")[0]},
            },
            "ticketNumber": str(number),
        }

        method_callable = lambda wallet, **kwargs: wallet.genericobject().insert(
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
        return response.json()

    async def create_link(
        self,
        qr_code: str,
        banner_link: str,
        event_name: str,
        end_date: datetime.datetime,
        nummer: int,
        event_date: datetime.datetime,
        locatie_naam: str,
    ) -> str:
        link_class = await self.create_class(
            event_name=event_name, event_date=event_date, locatie_naam=locatie_naam
        )
        link_object = await self.create_object(
            event_name=event_name,
            object_suffix=qr_code,
            qr_code=qr_code,
            banner_link=banner_link,
            end_date=end_date,
            number=nummer,
            event_date=event_date,
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
    service_file: json, issuer_id: int, base_url: str, class_url: str, object_url: str
) -> Wallet:
    wallet = Wallet()
    await wallet._async_init(service_file, issuer_id, base_url, class_url, object_url)
    return wallet
