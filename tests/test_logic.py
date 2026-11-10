from core.pages import canonical_domain
from core.redirects import build_redirects


def test_canonical_prefers_bare_domain() -> None:
    """The bare domain wins over www, and www is used when it is the only one."""
    assert canonical_domain(["www.example.com", "example.com"]) == "example.com"
    assert canonical_domain(["www.example.com"]) == "www.example.com"
    assert canonical_domain([]) is None


def test_build_redirects() -> None:
    """pages.dev (with previews) and www both redirect to the canonical domain."""
    items = build_redirects("site.pages.dev", ["example.com", "www.example.com"], "example.com")
    redirects = {item["redirect"]["source_url"]: item["redirect"] for item in items}
    assert set(redirects) == {"site.pages.dev", "www.example.com"}
    assert redirects["site.pages.dev"]["include_subdomains"] is True
    assert redirects["www.example.com"]["include_subdomains"] is False
    assert all(r["target_url"] == "https://example.com" and r["status_code"] == 301 for r in redirects.values())
