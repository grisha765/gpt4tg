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


async def search_4get(query: str, search_type: str = 'web') -> list:
    data_str = str()
    async with Common.client_ssl.stream(
        method='GET',
        url=f"{config.Config.api_url_4get}/api/v1/{search_type}",
        params={'s': query},
        timeout=30.0
    ) as executed:
        async for chunk in executed.aiter_bytes():
            data_str += chunk.decode('utf-8', errors='ignore')
    try:
        data = json.loads(data_str)
    except json.JSONDecodeError:
        return []

    web_data = extract_urls(data)
    print(web_data)
    return web_data


async def google_search(query: str, search_type: str) -> list[str]:
    """
    search from google.
    query : str
        human-readable search request.
    search_type : {'web', 'images', 'videos', 'news'}
        which google endpoint to call.
    example for search python version:
    await google_search(query='latest version of python', search_type='web')
    """
    logging.debug(f'<internet {search_type} search> {query}')
    try:
        data = await search_4get(query, search_type)
    except Exception as e:
        logging.error(e)
        return [f"Error request: {e}"]
    return data


if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")

