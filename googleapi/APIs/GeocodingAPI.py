import aiohttp


class Geocoding:
    def __init__(self, api_key: str) -> None:
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        self.api_key = api_key

    async def get_coordinates(self, address: str) -> (float, float):
        parameters = {"address": address, "key": self.api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=parameters) as response:
                if response.status != 200:
                    raise Exception(
                        f"Request failed with status code {response.status}"
                    )

                data = await response.json()

                if data["status"] != "OK":
                    raise Exception(f"Geocoding failed: {data.get('status')}")

                location = data.get("results")[0].get("geometry").get("location")
                return location.get("lat"), location.get("lng")
