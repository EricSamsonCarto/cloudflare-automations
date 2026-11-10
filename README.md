# cloudflare-automations
Python scripts for deploying and managing Cloudflare Pages projects.

## Scripts

Set the variables at the top of a script, then run it. Each one starts as a dry run that prints what it would change. Set `APPLY = True` to make the changes. Neither script deletes or replaces anything; they only add what's missing.

- `src/redirect_to_custom_domains.py` goes through every Pages project that has a custom domain. It redirects the project's `pages.dev` address, its preview URLs, and `www` to that domain with a 301, and turns off preview builds.
- `src/deploy_pages.py` creates a new Git-connected Pages project with the Conness GIS build settings. It attaches the domain and `www`, adds their DNS records, and sets up the same redirects. By default it turns preview builds off and puts preview URLs behind a Cloudflare Access policy for the emails you list.

## Cloudflare credentials

Put both values in a `.env` file at the repo root. It's gitignored, so it won't be committed.

- `CF_ACCOUNT_ID`: in the Cloudflare dashboard, open any domain and find the Account ID in the right sidebar of the Overview page. It's also the ID in the dashboard URL (`dash.cloudflare.com/<account-id>/...`).
- `CF_API_TOKEN`: go to [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens), choose Create Token, then Create Custom Token, and grant:
  - Account → Cloudflare Pages → Edit
  - Account → Account Filter Lists → Edit
  - Account → Account Rulesets → Edit
  - Account → Access: Apps and Policies → Edit
  - Zone → DNS → Edit
  - Zone → Zone → Read

  Scope it to your account and to the zones you use. Cloudflare shows the token only once.
