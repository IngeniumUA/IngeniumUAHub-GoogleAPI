import aiohttp
from fastapi import HTTPException


class Places:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://places.googleapis.com/v1/places"

    async def get_coordinates_from_place(self, place: str) -> tuple[float, float]:
        """
        Returns the latitude and longitude of the given place.
        :param place: The place to get coordinates from.
        :return: Coordinates as (lat, lng)
        """
        url = f"{self.base_url}:searchText"

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "places.location",
        }

        json_payload = {"textQuery": place}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, headers=headers, json=json_payload
            ) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Request failed with status code {response.status}",
                    )

                data = await response.json()
                places = data.get("places")
                if places is None:
                    raise HTTPException(
                        status_code=406,
                        detail="No location found for the given place.",
                    )
                location = places[0].get("location")
                return location.get("latitude"), location.get("longitude")
