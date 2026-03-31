import os
import time
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
    p = url.strip("/").split("/")
    return p[2], p[3], p[4]

def get_items(platform, owner, name, kind):
    items = []
    page = 1
    while page < 3:
        try:
            if platform == "github.com":
                url = f"https://api.github.com/repos/{owner}/{name}/{kind}?state=all&per_page=100&page={page}"
                headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
            else:
                url = f"https://repo.getmonero.org/api/v1/repos/{owner}/{name}/{kind}?state=all&per_page=100&page={page}"
                headers = {}
            res = requests.get(url, headers=headers, timeout=8)
            data = res.json()
            if not isinstance(data, list): break
            if len(data) == 0: break
            items += data
            page += 1
            time.sleep(0.2)
        except:
            break
    return items

def make_md(item, repo_url, kind):
    now = datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z"
    n = item["number"]
    title = item["title"]
    status = item["state"]
    link = item["html_url"]
    author = item["user"]["login"]
    created = item["created_at"]
    body = item.get("body") or ""

    if kind == "pulls":
        if item.get("merged_at"):
            status = "merged"
        if item.get("draft"):
            status = f"draft/{status}"

    t = "Issue" if kind == "issues" else "PullRequest"
    return f"""---
original_url: {link}
sync_time: {now}
repo_url: {repo_url}
type: {t}
status: {status}
number: {n}
title: {title}
---
# {title}
author: {author}
created_at: {created}
status: {status}

{body}
"""

for repo_url in repos:
    try:
        pf, owner, name = parse(repo_url)
        branch = name
        os.system(f"git checkout -b {branch} || git checkout {branch}")
        os.makedirs("issues", exist_ok=True)
        os.makedirs("pull_requests", exist_ok=True)

        items = get_items(pf, owner, name, "issues")
        for i in items:
            with open(f"issues/{i['number']}.md", "w", encoding="utf-8") as f:
                f.write(make_md(i, repo_url, "issues"))

        items = get_items(pf, owner, name, "pulls")
        for i in items:
            with open(f"pull_requests/{i['number']}.md", "w", encoding="utf-8") as f:
                f.write(make_md(i, repo_url, "pulls"))

        os.system("git add .")
        os.system(f'git commit -m "update"')
        os.system(f"git push origin {branch} --force")
    except:
        continue