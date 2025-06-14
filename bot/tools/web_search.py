import json
from bot.core.common import Common
from bot.config import logging_config, config
logging = logging_config.setup_logging(__name__)


async def search_4get(query: str) -> list:
    data_str = str()
    async with Common.client_ssl.stream(
        method='GET',
        url=config.Config.api_url_4get,
        params={'s': query},
        timeout=30.0
    ) as executed:
        async for chunk in executed.aiter_bytes():
            data_str += chunk.decode('utf-8', errors='ignore')
    try:
        data = json.loads(data_str)
    except json.JSONDecodeError:
        return []

    web_data = data.get('web', [])
    simplified_list = []
    for item in web_data:
        simplified_list.append({
            'title': item.get('title', ''),
            'description': item.get('description', ''),
            'url': item.get('url', '')
        })
    return simplified_list


async def google_search(query: str) -> list[str]:
    """
    search from google.
    example for search python version:
    await google_search(query='latest version of python')
    """
    logging.debug(f'<internet search> {query}')
    try:
        data = await search_4get(query)
    except Exception as e:
        logging.error(e)
        return [f"Error request: {e}"]
    return [item['url'] for item in data if item.get('url')]


if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")

