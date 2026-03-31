import os
import time
import git
import requests
from datetime import datetime, timezone

repos = [
    "https://repo.getmonero.org/monero-project/ccs-front",
    "https://repo.getmonero.org/monero-project/ccs-back",
    "https://repo.getmonero.org/monero-project/ccs-proposals",
    "https://github.com/monero-project/monero",
    "https://github.com/monero-project/monero-docs",
    "https://github.com/monero-project/monero-gui",
    "https://github.com/monero-project/monero-site",
    "https://github.com/monero-project/gitian.sigs",
    "https://github.com/monero-project/meta",
    "https://github.com/monero-project/guix",
    "https://github.com/monero-project/research-lab",
    "https://github.com/monero-project/guix.sigs",
    "https://github.com/monero-project/xmr-seeder",
    "https://github.com/monero-project/monero-forum"
]

def parse(url):
    p = url.strip('/').split('/')
    return p[2], p[3], p[4]

def headers(platform):
    if platform == "github.com":
        return {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
    return {}

def fetch(platform, owner, name, kind):
    items = []
    page = 1
    while True:
        if platform == "github.com":
            u = f"https://api.github.com/repos/{owner}/{name}/{kind}?state=all&per_page=100&page={page}"
        else:
            u = f"https://repo.getmonero.org/api/v1/repos/{owner}/{name}/{kind}?state=all&per_page=100&page={page}"
        r = requests.get(u, headers=headers(platform), timeout=20)
        if r.status_code != 200:
            break
        data = r.json()
        if not data:
            break
        items.extend(data)
        page += 1
        time.sleep(0.5)
    return items

def render(item, repo_url, kind):
    tz = datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z"
    num = item["number"]
    title = item["title"]
    status = item["state"]
    link = item["html_url"]
    created = item["created_at"]
    author = item["user"]["login"]
    body = item.get("body") or ""

    if kind == "pulls":
        if item.get("merged_at"):
            status = "merged"
        if item.get("draft"):
            status = f"draft/{status}"

    type_str = "Issue" if kind == "issues" else "PullRequest"

    return f"""---
original_url: {link}
sync_time: {tz}
repo_url: {repo_url}
type: {type_str}
status: {status}
number: {num}
title: {title}
---

# {title}
author: {author}
created_at: {created}
status: {status}

{body}
"""

def main():
    local = git.Repo(".")
    for url in repos:
        try:
            platform, owner, name = parse(url)
            branch = name
            print(f"Processing {name}")

            if branch in local.branches:
                local.git.checkout(branch)
            else:
                local.git.checkout("-b", branch)

            os.makedirs("issues", exist_ok=True)
            os.makedirs("pull_requests", exist_ok=True)

            issues = fetch(platform, owner, name, "issues")
            for i in issues:
                path = f"issues/{i['number']}.md"
                with open(path, "w", encoding="utf-8") as f:
                    f.write(render(i, url, "issues"))

            prs = fetch(platform, owner, name, "pulls")
            for pr in prs:
                path = f"pull_requests/{pr['number']}.md"
                with open(path, "w", encoding="utf-8") as f:
                    f.write(render(pr, url, "pulls"))

            local.git.add(".")
            try:
                local.git.commit(m=f"Sync {name}")
                local.git.push("origin", branch)
            except git.exc.GitCommandError:
                pass
        except Exception as e:
            print(f"Failed {name}: {e}")

if __name__ == "__main__":
    main()