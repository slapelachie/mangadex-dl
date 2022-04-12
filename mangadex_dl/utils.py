import requests
from time import sleep, time


def get_mangadex_request(url: str):
    response = requests.get(url)

    while response.status_code == 429:
        wait_time = int(
            int(response.headers.get("x-ratelimit-retry-after", int(time() + 60)))
            - time()
        )

        print(f"Exceeded rate-limit, waiting {wait_time} seconds")
        sleep(wait_time)

        response = requests.get(url)

    if response.status_code != 200:
        raise ValueError("Response was not successfull!")

    sleep(1)
    return response


def get_mangadex_response(url: str):
    response = get_mangadex_request(url)
    return response.json()
