# Security policy

## Supported versions

Only the `main` branch is supported. It is what runs on [aaron404.com](https://aaron404.com), and every merge to it is deployed.

## Reporting a vulnerability

Please **do not** open a public issue or pull request for a security problem.

Report it privately through GitHub instead: go to the repository's **Security** tab and choose **Report a vulnerability**, or open [a private report directly](https://github.com/wu-changxing/macaw/security/advisories/new). Only the maintainer can see it.

Please include:

- what is affected (a URL path, a file, or a setting);
- how to reproduce it, as a minimal request or steps;
- what an attacker could do with it.

This is a one-person project; the maintainer aims to acknowledge reports within a week. Once a fix is deployed, the advisory is published with credit to you, unless you prefer not to be named.

## Scope

In scope: the code in this repository and how it behaves on aaron404.com. For example, the sign-to-comment endpoint, subscriptions, the admin login, the API and the SEO endpoints. [docs/architecture.md](docs/architecture.md) describes how they are meant to be protected.

Out of scope:

- denial of service by sheer volume, and automated scanner output without a demonstrated impact;
- vulnerabilities in Django, Wagtail or other dependencies (report them upstream; tell us if aaron404.com is exposed and we will upgrade);
- missing best-practice headers with no concrete attack.

Please test only against your own local copy, never against the live site's data or its readers.
