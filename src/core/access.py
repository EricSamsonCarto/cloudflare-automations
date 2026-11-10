from cloudflare import Cloudflare

from core.client import announce


def protect_previews(client: Cloudflare, account_id: str, project: str, emails: list[str], apply: bool) -> None:
    """Put a project's preview URLs behind a Cloudflare Access policy for the given emails.

    Mirrors the dashboard's "Enable access policy" setting by protecting *.<project>.pages.dev.

    Args:
        client: The Cloudflare client.
        account_id: The Cloudflare account ID.
        project: The Pages project name.
        emails: Email addresses allowed to view previews.
        apply: Whether to create the Access application or only preview it.
    """
    domain = f"*.{project}.pages.dev"
    for app in client.zero_trust.access.applications.list(account_id=account_id):
        if getattr(app, "domain", None) == domain:
            print(f"SKIP: Access application for {domain} already exists")
            return
    if not announce(f"restrict {domain} to {', '.join(emails)} with Cloudflare Access", apply):
        return
    client.zero_trust.access.applications.create(
        account_id=account_id,
        type="self_hosted",
        name=f"{project} previews",
        domain=domain,
        policies=[
            {
                "name": "Allowed viewers",
                "decision": "allow",
                "include": [{"email": {"email": email}} for email in emails],
            }
        ],
    )
