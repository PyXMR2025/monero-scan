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
    p = url.strip('/').split('/')
    return p[2], p[3], p[4]

def fetch(platform, owner, name, kind):
    items = []
    page = 1
    for _ in range(5):
        try:
            if platform == "github.com":
                u = f"https://api.github.com/repos/{owner}/{name}/{kind}?state=all&per_page=100&page={page}"
                h = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
            else:
                u = f"https://repo.getmonero.org/api/v1/repos/{owner}/{name}/{kind}?state=all&per_page=100&page={page}"
                h = {}
            r = requests.get(u, headers=h, timeout=10)
            if r.status_code != 200:
                break
            data = r.json()
            if not data:
                break
            items.extend(data)
            page +=1
            time.sleep(0.3)
        except:
            break
    return items

def build(item, repo_url, kind):
    t = datetime.now(timezone.utc).isoformat(timespec="seconds")+"Z"
    num = item["number"]
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
    
    typ = "Issue" if kind == "issues" else "PullRequest"
    return f"""---
original_url: {link}
sync_time: {t}
repo_url: {repo_url}
type: {typ}
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

def git(cmd):
    os.system(cmd)

for url in repos:
    try:
        platform, owner, name = parse(url)
        branch = name
        git(f"git checkout -b {branch} || git checkout {branch}")
        os.makedirs("issues", exist_ok=True)
        os.makedirs("pull_requests", exist_ok=True)

        for i in fetch(platform, owner, name, "issues"):
            with open(f"issues/{i['number']}.md", "w", encoding="utf-8") as f:
                f.write(build(i, url, "issues"))

        for pr in fetch(platform, owner, name, "pulls"):
            with open(f"pull_requests/{pr['number']}.md", "w", encoding="utf-8") as f:
                f.write(build(pr, url, "pulls"))

        git("git add .")
        git(f'git commit -m "Sync {branch}"')
        git(f"git push origin {branch} -f")
    except:
        continue