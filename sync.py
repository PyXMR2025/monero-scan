import os
import time
import requests

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
    try:
        if platform == "github.com":
            u = f"https://api.github.com/repos/{owner}/{name}/{kind}?state=all&per_page=20"
            h = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
        else:
            u = f"https://repo.getmonero.org/api/v1/repos/{owner}/{name}/{kind}?state=all&per_page=20"
            h = {}
        r = requests.get(u, headers=h, timeout=10)
        print(f"[{platform}] {kind} status: {r.status_code}")
        return r.json() if r.status_code == 200 else []
    except:
        return []

def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

for url in repos:
    try:
        pf, owner, name = parse(url)
        branch = name
        os.system(f"git checkout -b {branch} || git checkout {branch}")
        
        os.makedirs("issues", exist_ok=True)
        os.makedirs("pull_requests", exist_ok=True)

        write_file("test.md", "test")

        items = fetch(pf, owner, name, "issues")
        print(f"{name} issues: {len(items)}")
        for i in items:
            write_file(f"issues/{i['number']}.md", i['title'])

        items = fetch(pf, owner, name, "pulls")
        print(f"{name} pulls: {len(items)}")
        for i in items:
            write_file(f"pull_requests/{i['number']}.md", i['title'])

        os.system("git add .")
        os.system("git commit -m sync")
        os.system(f"git push origin {branch} -f")
    except Exception as e:
        print(f"error: {e}")
        continue