import aiohttp
from fastapi import HTTPException


class Geocoding:
    def __init__(self, api_key: str) -> None:
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        self.api_key = api_key

    async def get_coordinates_from_address(self, address: str) -> tuple[float, float]:
        """
        Returns the coordinates of the given address.
        :param address: Address to geocode
        :return: Tuple of latitude and longitude (latitude, longitude)
        """
        parameters = {"address": address, "key": self.api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=parameters) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Request failed with status code {response.status}",
                    )

                data = await response.json()

                if data["status"] != "OK":
                    raise HTTPException(
                        status_code=400,
                        detail=f"Geocoding failed: {data['status']}.",
                    )

                location = data.get("results")[0].get("geometry").get("location")
                return location.get("lat"), location.get("lng")

    async def get_address_from_coordinates(
        self, latitude: float, longitude: float
    ) -> str:
        """
        Returns the address from the given coordinates.
        :param latitude: Latitude of the location
        :param longitude: Longitude of the location
        :return: The address corresponding to the given coordinates
        """
        parameters = {
            "latlng": f"{latitude},{longitude}",
            "key": self.api_key,
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=parameters) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Request failed with status code {response.status}",
                    )

                data = await response.json()

                if data["status"] != "OK":
                    raise HTTPException(
                        status_code=400,
                        detail=f"Geocoding failed: {data['status']}.",
                    )

                location = data.get("results")[0].get("formatted_address")
                return location
