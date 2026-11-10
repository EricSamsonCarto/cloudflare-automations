import json

import httpx

from core.access import protect_previews
from core.client import get_client


def test_protect_previews_creates_access_app() -> None:
    """A new Access app covers the project's preview subdomains and allows only the listed emails."""
    sent = []

    def respond(request: httpx.Request) -> httpx.Response:
        """Record each request and answer with an empty Cloudflare result."""
        sent.append(request)
        if request.method == "GET":
            return httpx.Response(200, json={"success": True, "errors": [], "messages": [], "result": []})
        return httpx.Response(200, json={"success": True, "errors": [], "messages": [], "result": {}})

    client = get_client("token", transport=httpx.MockTransport(respond))
    protect_previews(client, "acct", "site", ["me@example.com"], apply=True)
    body = json.loads(sent[-1].content)
    assert sent[-1].method == "POST"
    assert body["domain"] == "*.site.pages.dev"
    assert body["policies"][0]["include"] == [{"email": {"email": "me@example.com"}}]
