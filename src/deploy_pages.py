from core.access import protect_previews
from core.client import (
    get_client,
    load_credentials,
)
from core.dns import (
    ensure_cname,
    find_zone_id,
)
from core.pages import (
    attach_domain,
    create_git_project,
    project_exists,
)
from core.redirects import (
    add_redirects,
    build_redirects,
    ensure_redirect_rule,
    find_or_create_list,
)


REPO = "owner/repo"
PROJECT = "my-site"
DOMAIN = "example.com"
APP_PROJECT = PROJECT
BRANCH = "main"
PREVIEW_DEPLOYMENTS = "none"
PREVIEW_ACCESS_EMAILS = ["you@example.com"]
APPLY = False


def main(
    repo: str,
    project: str,
    domain: str,
    app_project: str,
    branch: str,
    preview_setting: str,
    access_emails: list[str],
    apply: bool,
) -> None:
    """Create a Git-connected Pages site with its custom domain, www, and redirects.

    Args:
        repo: The GitHub repository as owner/name.
        project: The Pages project name (lowercase letters, digits, hyphens).
        domain: The bare domain, whose zone must be in this account.
        app_project: The folder under app/projects to build.
        branch: The production branch.
        preview_setting: Which branches build previews: "none", "all", or "custom".
        access_emails: Emails allowed to view previews through Cloudflare Access; empty skips Access.
        apply: Whether to make the changes or only print what would change.
    """
    token, account_id = load_credentials()
    client = get_client(token)
    if project_exists(client, account_id, project):
        raise SystemExit(f"Pages project {project} already exists. Nothing changed.")
    zone_id = find_zone_id(client, account_id, domain)
    if zone_id is None:
        raise SystemExit(f"No zone for {domain} in this account. Nothing changed.")

    pages_subdomain = f"{project}.pages.dev"
    domains = [domain, f"www.{domain}"]
    create_git_project(client, account_id, project, repo, branch, app_project, preview_setting, apply)
    if access_emails:
        protect_previews(client, account_id, project, access_emails, apply)
    for hostname in domains:
        attach_domain(client, account_id, project, hostname, apply)
        ensure_cname(client, zone_id, hostname, pages_subdomain, apply)

    list_id = find_or_create_list(client, account_id, apply)
    add_redirects(client, account_id, list_id, build_redirects(pages_subdomain, domains, domain), apply)
    ensure_redirect_rule(client, account_id, apply)
    if apply:
        print(f"\nDone. Push to {branch} to trigger the first build.")
    else:
        print("\nDry run only. Set APPLY = True to make these changes.")


if __name__ == "__main__":
    main(REPO, PROJECT, DOMAIN, APP_PROJECT, BRANCH, PREVIEW_DEPLOYMENTS, PREVIEW_ACCESS_EMAILS, APPLY)
