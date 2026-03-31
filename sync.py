import os
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

def get_data(platform, owner, name, typ):
    try:
        if platform == "github.com":
            url = f"https://api.github.com/repos/{owner}/{name}/{typ}?state=all&per_page=5"
            headers = {}
        else:
            url = f"https://repo.getmonero.org/api/v1/repos/{owner}/{name}/{typ}?state=all&per_page=5"
            headers = {}
        res = requests.get(url, headers=headers, timeout=10)
        return res.json() if res.status_code == 200 else []
    except:
        return []

for repo_url in repos:
    try:
        pf, owner, name = parse(repo_url)
        branch = name
        
        os.system(f"git checkout -b {branch} || git checkout {branch}")
        os.makedirs("issues", exist_ok=True)
        os.makedirs("pull_requests", exist_ok=True)

        with open("test.md", "w") as f:
            f.write("synced")
        
        with open("issues/sample.md", "w") as f:
            f.write(f"repo: {name}")
        
        with open("pull_requests/sample.md", "w") as f:
            f.write(f"repo: {name}")

        items = get_data(pf, owner, name, "issues")
        for item in items:
            with open(f"issues/{item['number']}.md", "w") as f:
                f.write(item["title"])

        items = get_data(pf, owner, name, "pulls")
        for item in items:
            with open(f"pull_requests/{item['number']}.md", "w") as f:
                f.write(item["title"])

        os.system("git add .")
        os.system("git commit -m sync")
        os.system(f"git push origin {branch} -f")
    except:
        continue