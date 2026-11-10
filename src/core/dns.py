from cloudflare import Cloudflare

from core.client import announce


def find_zone_id(client: Cloudflare, account_id: str, domain: str) -> str | None:
    """Find the ID of the account's zone for a bare domain.

    Args:
        client: The Cloudflare client.
        account_id: The Cloudflare account ID.
        domain: The bare domain, such as example.com.

    Returns:
        The zone ID, or None if the zone is not in this account.
    """
    zones = list(client.zones.list(name=domain, account={"id": account_id}))
    return zones[0].id if zones else None


def ensure_cname(client: Cloudflare, zone_id: str, name: str, target: str, apply: bool) -> None:
    """Create a proxied CNAME record unless any record already exists for that name.

    Args:
        client: The Cloudflare client.
        zone_id: The zone ID.
        name: The record name, such as www.example.com.
        target: The CNAME target, such as project.pages.dev.
        apply: Whether to create the record or only preview it.
    """
    if list(client.dns.records.list(zone_id=zone_id, name={"exact": name})):
        print(f"SKIP: DNS record for {name} already exists, left unchanged")
        return
    if announce(f"create CNAME {name} -> {target}", apply):
        client.dns.records.create(zone_id=zone_id, name=name, type="CNAME", content=target, proxied=True)
