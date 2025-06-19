import json
from bot.core.common import Common
from bot.config import logging_config, config
logging = logging_config.setup_logging(__name__)


def extract_urls(obj) -> list:
    urls = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "url":
                if value:
                    urls.append(value)
            else:
                urls.extend(extract_urls(value))
    elif isinstance(obj, list):
        for item in obj:
            urls.extend(extract_urls(item))

    return urls


async def search_4get(query: str, search_type: str, pages: int = 1) -> list:
    aggregated_urls = []
    next_token = None

    for _ in range(max(1, pages)):
        params = {"s": query} if next_token is None else {"npt": next_token}

        data_str = ""
        async with Common.client_ssl.stream(
            method="GET",
            url=f"{config.Config.api_url_4get}/api/v1/{search_type}",
            params=params,
            timeout=30.0,
        ) as executed:
            async for chunk in executed.aiter_bytes():
                data_str += chunk.decode("utf-8", errors="ignore")

        try:
            data = json.loads(data_str)
        except json.JSONDecodeError:
            logging.warning("Failed to decode JSON from 4get response.")
            break

        aggregated_urls.extend(extract_urls(data))
        next_token = data.get("npt")

        if next_token is None:
            break

    return aggregated_urls


async def google_search(query: str, search_type: str, pages: int) -> list[str]:
    """
    search from google.
    query : str
        human-readable search request.
    search_type : {'web', 'images', 'videos', 'news'}
        which google endpoint to call.
    pages : int
        number of result pages to retrieve.
    example for search python version:
    await google_search(query='latest version of python', search_type='web', pages=1)
    """
    logging.debug(f'<internet {search_type} search> {query} (pages={pages})')
    try:
        data = await search_4get(query, search_type, pages)
    except Exception as e:
        logging.error(e)
        return [f"Error request: {e}"]
    return data


if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")

