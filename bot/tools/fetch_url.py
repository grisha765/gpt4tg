from bot.core.common import Common
from bot.config import logging_config
logging = logging_config.setup_logging(__name__)


async def fetch_text_content(url: str) -> str:
    data_str = str()
    async with Common.client_ssl.stream(
        method='GET',
        url=url,
        timeout=30.0
    ) as executed:
        async for chunk in executed.aiter_bytes():
            data_str += chunk.decode('utf-8', errors='ignore')

    markdown_content = Common.converter.handle(data_str)
    return markdown_content


async def open_url_find(url: str, phrase: str, window: int = 400) -> str:
    """
    fetch the page, searches for 'phrase' and returns a small fragment
    of text around the first match.
    if the phrase cannot be found, returns the beginning of the page (window * 2).
    example for fetch information and search by a specific phrase from python.org website:
    await open_url_find(url='https://www.python.org', phrase='latest news', window=400)
    """
    logging.debug(f"<fetch url / find> {url} / {phrase}")
    try:
        full_text = await fetch_text_content(url)
    except Exception as e:
        logging.error(e)
        return f"Error request: {e}"
    idx = full_text.lower().find(phrase.lower())
    if idx == -1:
        return full_text[: window * 2]
    start = max(0, idx - window)
    end = min(len(full_text), idx + len(phrase) + window)
    return full_text[start:end]


async def open_url(url: str) -> str:
    """
    fetch information from url.
    example for fetch information from python.org website:
    await open_url(url='https://www.python.org')
    """
    logging.debug(f'<fetch url> {url}')
    try:
        text = await fetch_text_content(url)
    except Exception as e:
        logging.error(e)
        return f"Error request: {e}"
    return text[:15000]


if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")

