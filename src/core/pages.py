from cloudflare import Cloudflare, NotFoundError
from cloudflare.types.pages import Project

from core.client import announce


def list_projects(client: Cloudflare, account_id: str) -> list[Project]:
    """Fetch every Pages project in the account.

    Args:
        client: The Cloudflare client.
        account_id: The Cloudflare account ID.

    Returns:
        All Pages projects.
    """
    return list(client.pages.projects.list(account_id=account_id))


def project_exists(client: Cloudflare, account_id: str, name: str) -> bool:
    """Check whether a Pages project name is already taken in the account.

    Args:
        client: The Cloudflare client.
        account_id: The Cloudflare account ID.
        name: The Pages project name.

    Returns:
        True if the project exists.
    """
    try:
        client.pages.projects.get(name, account_id=account_id)
    except NotFoundError:
        return False
    return True


def custom_domains(project: Project) -> list[str]:
    """List a project's custom domains, leaving out its pages.dev address.

    Args:
        project: The Pages project.

    Returns:
        The custom domain names.
    """
    return [domain for domain in project.domains or [] if not domain.endswith(".pages.dev")]


def canonical_domain(domains: list[str]) -> str | None:
    """Pick the domain a site should redirect to, preferring a bare domain over www.

    Args:
        domains: The project's custom domains.

    Returns:
        The canonical domain, or None if there are no custom domains.
    """
    bare = [domain for domain in domains if not domain.startswith("www.")]
    return (bare or domains or [None])[0]


def disable_previews(client: Cloudflare, account_id: str, project: Project, apply: bool) -> None:
    """Stop a Git-connected project from building preview deployments.

    The full existing source config is sent back with only the preview setting changed.

    Args:
        client: The Cloudflare client.
        account_id: The Cloudflare account ID.
        project: The Pages project.
        apply: Whether to make the change or only preview it.
    """
    if project.source is None:
        print(f"SKIP: {project.name} is not Git-connected, previews unchanged")
        return
    source = project.source.model_dump(exclude_none=True)
    if source["config"].get("preview_deployment_setting") == "none":
        print(f"SKIP: {project.name} previews already disabled")
        return
    source["config"]["preview_deployment_setting"] = "none"
    if announce(f"disable preview builds for {project.name}", apply):
        client.pages.projects.edit(project.name, account_id=account_id, source=source)


def create_git_project(
    client: Cloudflare,
    account_id: str,
    name: str,
    repo: str,
    branch: str,
    app_project: str,
    apply: bool,
) -> None:
    """Create a Git-connected Pages project using the Conness GIS build settings.

    Args:
        client: The Cloudflare client.
        account_id: The Cloudflare account ID.
        name: The Pages project name.
        repo: The GitHub repository as owner/name.
        branch: The production branch.
        app_project: The folder under app/projects to build.
        apply: Whether to create the project or only preview it.
    """
    owner, repo_name = repo.split("/", 1)
    env_vars = {"env_vars": {"NODE_VERSION": {"type": "plain_text", "value": "24"}}}
    if not announce(f"create Pages project {name} from {repo}@{branch}", apply):
        return
    client.pages.projects.create(
        account_id=account_id,
        name=name,
        production_branch=branch,
        build_config={
            "build_command": f"npm ci && npm run build {app_project}",
            "destination_dir": f"dist/{app_project}",
            "root_dir": "app",
        },
        deployment_configs={"production": env_vars, "preview": env_vars},
        source={
            "type": "github",
            "config": {
                "owner": owner,
                "repo_name": repo_name,
                "production_branch": branch,
                "deployments_enabled": True,
                "production_deployments_enabled": True,
                "preview_deployment_setting": "none",
                "pr_comments_enabled": False,
                "path_includes": ["app/*"],
                "path_excludes": ["app/projects/_*"],
            },
        },
    )


def attach_domain(client: Cloudflare, account_id: str, project_name: str, domain: str, apply: bool) -> None:
    """Attach a custom domain to a Pages project.

    Args:
        client: The Cloudflare client.
        account_id: The Cloudflare account ID.
        project_name: The Pages project name.
        domain: The domain to attach.
        apply: Whether to attach it or only preview it.
    """
    if announce(f"attach {domain} to {project_name}", apply):
        client.pages.projects.domains.create(project_name, account_id=account_id, name=domain)
