import time

from cloudflare import Cloudflare, NotFoundError

from core.client import announce


LIST_NAME = "pages_dev_redirects"
PHASE = "http_request_redirect"


def build_redirects(pages_subdomain: str, domains: list[str], canonical: str) -> list[dict]:
    """Build bulk redirect entries that send a project's other hostnames to its canonical domain.

    The pages.dev entry includes subdomains so preview URLs redirect too.

    Args:
        pages_subdomain: The project's pages.dev hostname.
        domains: The project's custom domains.
        canonical: The domain everything should redirect to.

    Returns:
        Bulk redirect list items.
    """
    target = f"https://{canonical}"
    sources = [(pages_subdomain, True)] + [(domain, False) for domain in domains if domain != canonical]
    return [
        {
            "redirect": {
                "source_url": source,
                "target_url": target,
                "status_code": 301,
                "include_subdomains": include_subdomains,
                "subpath_matching": True,
                "preserve_path_suffix": True,
                "preserve_query_string": True,
            }
        }
        for source, include_subdomains in sources
    ]


def find_or_create_list(client: Cloudflare, account_id: str, apply: bool) -> str | None:
    """Find the shared bulk redirect list, creating it if it does not exist.

    Args:
        client: The Cloudflare client.
        account_id: The Cloudflare account ID.
        apply: Whether to create the list or only preview it.

    Returns:
        The list ID, or None when the list would be created in a dry run.
    """
    for existing in client.rules.lists.list(account_id=account_id):
        if existing.name == LIST_NAME:
            return existing.id
    if not announce(f"create bulk redirect list {LIST_NAME}", apply):
        return None
    return client.rules.lists.create(account_id=account_id, kind="redirect", name=LIST_NAME).id


def existing_sources(client: Cloudflare, account_id: str, list_id: str | None) -> set[str]:
    """Collect the source URLs already in the bulk redirect list.

    Args:
        client: The Cloudflare client.
        account_id: The Cloudflare account ID.
        list_id: The list ID, or None if the list does not exist yet.

    Returns:
        The source URLs present in the list.
    """
    if list_id is None:
        return set()
    return {item.redirect.source_url for item in client.rules.lists.items.list(list_id, account_id=account_id)}


def add_redirects(client: Cloudflare, account_id: str, list_id: str | None, items: list[dict], apply: bool) -> None:
    """Append new entries to the bulk redirect list, skipping sources it already has.

    Args:
        client: The Cloudflare client.
        account_id: The Cloudflare account ID.
        list_id: The list ID, or None if the list does not exist yet.
        items: Bulk redirect list items to add.
        apply: Whether to add them or only preview them.
    """
    present = existing_sources(client, account_id, list_id)
    new_items = [item for item in items if item["redirect"]["source_url"] not in present]
    for item in items:
        if item not in new_items:
            print(f"SKIP: redirect from {item['redirect']['source_url']} already exists")
    for item in new_items:
        announce(f"redirect {item['redirect']['source_url']} -> {item['redirect']['target_url']}", apply)
    if not new_items or not apply:
        return
    operation_id = client.rules.lists.items.create(list_id, account_id=account_id, body=new_items).operation_id
    wait_for_operation(client, account_id, operation_id)


def wait_for_operation(client: Cloudflare, account_id: str, operation_id: str, timeout: float = 60) -> None:
    """Wait for an asynchronous bulk list operation to finish.

    Args:
        client: The Cloudflare client.
        account_id: The Cloudflare account ID.
        operation_id: The bulk operation ID.
        timeout: Seconds to wait before giving up.

    Raises:
        RuntimeError: If the operation fails or does not finish in time.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        operation = client.rules.lists.bulk_operations.get(operation_id, account_id=account_id)
        if operation.status == "completed":
            return
        if operation.status == "failed":
            raise RuntimeError(f"Bulk redirect update failed: {operation.error}")
        time.sleep(2)
    raise RuntimeError(f"Bulk redirect update {operation_id} did not finish within {timeout}s")


def ensure_redirect_rule(client: Cloudflare, account_id: str, apply: bool) -> None:
    """Make sure an account redirect rule enables the shared list, without touching other rules.

    Args:
        client: The Cloudflare client.
        account_id: The Cloudflare account ID.
        apply: Whether to create the rule or only preview it.
    """
    rule = {
        "action": "redirect",
        "action_parameters": {"from_list": {"name": LIST_NAME, "key": "http.request.full_uri"}},
        "expression": f"http.request.full_uri in ${LIST_NAME}",
        "description": "Redirect pages.dev and www hostnames to custom domains",
        "enabled": True,
    }
    try:
        ruleset = client.rulesets.phases.get(PHASE, account_id=account_id)
    except NotFoundError:
        if announce(f"create account redirect ruleset with rule for {LIST_NAME}", apply):
            client.rulesets.create(account_id=account_id, kind="root", name="default", phase=PHASE, rules=[rule])
        return
    for existing in ruleset.rules:
        from_list = getattr(existing.action_parameters, "from_list", None)
        if from_list is not None and from_list.name == LIST_NAME:
            print(f"SKIP: redirect rule for {LIST_NAME} already exists")
            return
    if announce(f"add redirect rule for {LIST_NAME}", apply):
        client.rulesets.rules.create(ruleset.id, account_id=account_id, **rule)
