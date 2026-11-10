import os

import httpx
from cloudflare import Cloudflare
from dotenv import load_dotenv


BLOCKED_METHODS = frozenset({"DELETE", "PUT"})


def load_credentials() -> tuple[str, str]:
    """Load the API token and account ID from the repo's .env file.

    Returns:
        The API token and the account ID.

    Raises:
        SystemExit: If either value is missing.
    """
    load_dotenv()
    token = os.getenv("CF_API_TOKEN")
    account_id = os.getenv("CF_ACCOUNT_ID")
    if not token or not account_id:
        raise SystemExit("CF_API_TOKEN and CF_ACCOUNT_ID must be set in .env (see README).")
    return token, account_id


def block_destructive(request: httpx.Request) -> None:
    """Refuse any request that could delete or replace Cloudflare resources.

    Args:
        request: The outgoing HTTP request.

    Raises:
        PermissionError: If the request uses DELETE or PUT.
    """
    if request.method in BLOCKED_METHODS:
        raise PermissionError(f"Blocked {request.method} {request.url}: scripts may not delete or replace.")


def get_client(token: str, transport: httpx.BaseTransport | None = None) -> Cloudflare:
    """Build a Cloudflare client that can never send DELETE or PUT requests.

    Args:
        token: The Cloudflare API token.
        transport: Optional HTTP transport, used by tests.

    Returns:
        A configured Cloudflare client.
    """
    http_client = httpx.Client(event_hooks={"request": [block_destructive]}, transport=transport)
    return Cloudflare(api_token=token, http_client=http_client, max_retries=0)


def announce(action: str, apply: bool) -> bool:
    """Print a planned change and report whether it should be made.

    Args:
        action: A description of the change.
        apply: Whether changes are being applied or only previewed.

    Returns:
        The value of apply.
    """
    print(f"{'APPLY' if apply else 'DRY RUN'}: {action}")
    return apply
