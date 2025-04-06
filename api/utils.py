"""Utils for the app routes."""
import logging

from starlette.datastructures import URL


logger = logging.getLogger(__name__)


def ensure_ssl_for_ngrok(url: URL) -> URL:
    """Ensure that the URL is HTTPS for ngrok."""
    if "ngrok" in url.hostname and url.scheme == "http":
        logger.warning("Forcing HTTPS for ngrok")
        return url.replace(scheme="https")
    else:
        logger.debug("Not forcing HTTPS for ngrok")
        return url
