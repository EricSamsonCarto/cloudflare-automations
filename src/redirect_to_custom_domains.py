from core.client import (
    get_client,
    load_credentials,
)
from core.pages import (
    canonical_domain,
    custom_domains,
    disable_previews,
    list_projects,
)
from core.redirects import (
    add_redirects,
    build_redirects,
    ensure_redirect_rule,
    find_or_create_list,
)


def main(apply: bool) -> None:
    """Redirect every Pages project's pages.dev and www hostnames to its custom domain and disable previews.

    Args:
        apply: Whether to make the changes or only print what would change.
    """
    token, account_id = load_credentials()
    client = get_client(token)
    redirects = []
    for project in list_projects(client, account_id):
        domains = custom_domains(project)
        canonical = canonical_domain(domains)
        if canonical is None:
            print(f"SKIP: {project.name} has no custom domain")
            continue
        redirects += build_redirects(project.subdomain, domains, canonical)
        disable_previews(client, account_id, project, apply)

    list_id = find_or_create_list(client, account_id, apply)
    add_redirects(client, account_id, list_id, redirects, apply)
    ensure_redirect_rule(client, account_id, apply)
    if not apply:
        print("\nDry run only. Set APPLY = True to make these changes.")


if __name__ == "__main__":
    APPLY = True
    main(APPLY)
