import httpx
import pytest
from cloudflare import APIConnectionError

from core.client import (
    announce,
    block_destructive,
    get_client,
)


@pytest.mark.parametrize("method", ["DELETE", "PUT"])
def test_blocks_destructive_methods(method: str) -> None:
    """DELETE and PUT requests are refused."""
    with pytest.raises(PermissionError):
        block_destructive(httpx.Request(method, "https://api.cloudflare.com/x"))


@pytest.mark.parametrize("method", ["GET", "POST", "PATCH"])
def test_allows_safe_methods(method: str) -> None:
    """GET, POST, and PATCH requests pass through."""
    block_destructive(httpx.Request(method, "https://api.cloudflare.com/x"))


def test_client_never_sends_delete() -> None:
    """A delete through the real SDK client fails before reaching the network."""
    sent = []
    transport = httpx.MockTransport(lambda request: sent.append(request) or httpx.Response(200, json={}))
    client = get_client("token", transport=transport)
    with pytest.raises(APIConnectionError):
        client.pages.projects.delete("site", account_id="acct")
    assert sent == []


def test_announce_returns_apply(capsys: pytest.CaptureFixture[str]) -> None:
    """announce prints the action and passes apply through."""
    assert announce("do thing", False) is False
    assert "DRY RUN: do thing" in capsys.readouterr().out
