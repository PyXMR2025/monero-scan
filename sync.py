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

def fetch(platform, owner, name, kind):
    items = []
    page = 1
    while page < 4:
        try:
            if platform == "github.com":
                u = f"https://api.github.com/repos/{owner}/{name}/{kind}?state=all&per_page=100&page={page}"
                h = {}
            else:
                u = f"https://repo.getmonero.org/api/v1/repos/{owner}/{name}/{kind}?state=all&per_page=100&page={page}"
                h = {}
            r = requests.get(u, headers=h, timeout=10)
            if r.status_code != 200:
                break
            data = r.json()
            if not isinstance(data, list) or len(data) == 0:
                break
            items.extend(data)
            page += 1
            time.sleep(0.2)
        except:
            break
    return items

def build_md(item, repo_url, kind):
    now = datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z"
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
sync_time: {now}
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

for url in repos:
    try:
        pf, owner, name = parse(url)
        branch = name
        os.system(f"git checkout -b {branch} || git checkout {branch}")
        
        os.makedirs("issues", exist_ok=True)
        os.makedirs("pull_requests", exist_ok=True)

        for i in fetch(pf, owner, name, "issues"):
            with open(f"issues/{i['number']}.md", "w", encoding="utf-8") as f:
                f.write(build_md(i, url, "issues"))

        for pr in fetch(pf, owner, name, "pulls"):
            with open(f"pull_requests/{pr['number']}.md", "w", encoding="utf-8") as f:
                f.write(build_md(pr, url, "pulls"))

        os.system("git add .")
        os.system("git commit -m sync")
        os.system(f"git push origin {branch} -f")
    except:
        continue