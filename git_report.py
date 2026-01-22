import os
import json
import datetime as dt
import urllib.request
import urllib.parse
import urllib.error

API = "https://api.github.com"
PER_PAGE = 100

def gh_get(path, token, params=None, accept_topics=False):
    url = f"{API}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "simple-git-report",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if accept_topics:
        headers["Accept"] = "application/vnd.github+json"

    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read().decode("utf-8")
            return json.loads(data), resp.headers
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8")
        except Exception:
            pass
        raise RuntimeError(f"HTTP {e.code} em {path} | {body[:300]}") from e

def parse_link_header(link_header):
    if not link_header:
        return {}
    parts = [p.strip() for p in link_header.split(",")]
    out = {}
    for p in parts:
        if "; " in p:
            url_part, rel_part = p.split("; ", 1)
            url = url_part.strip("<>")
            rel = rel_part.split("=", 1)[1].strip('"')
            out[rel] = url
    return out

def paginate(path, token, params=None):
    page = 1
    all_items = []
    while True:
        p = dict(params or {})
        p["per_page"] = PER_PAGE
        p["page"] = page
        data, headers = gh_get(path, token, p)

        if not isinstance(data, list):
            raise RuntimeError(f"Esperava lista, veio {type(data)} em {path}")

        all_items.extend(data)
        links = parse_link_header(headers.get("Link"))
        if "next" in links:
            page += 1
        else:
            break
    return all_items

def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

def fetch_repos(owner, scope, token):
    scope = (scope or "user").lower()
    if scope == "org":
        return paginate(f"/orgs/{owner}/repos", token, {"type": "all", "sort": "updated", "direction": "desc"})
    return paginate(f"/users/{owner}/repos", token, {"type": "all", "sort": "updated", "direction": "desc"})

def fetch_topics(owner, repo, token):
    data, _ = gh_get(f"/repos/{owner}/{repo}/topics", token, accept_topics=True)
    return data.get("names", [])

def fetch_languages(owner, repo, token):
    data, _ = gh_get(f"/repos/{owner}/{repo}/languages", token)
    return data

def write_repo_detail(site_dir, owner, repo):
    repo_name = repo["name"]
    topics = []
    langs = {}
    try:
        topics = fetch_topics(owner, repo_name, os.environ["GH_TOKEN"])
    except Exception:
        topics = []
    try:
        langs = fetch_languages(owner, repo_name, os.environ["GH_TOKEN"])
    except Exception:
        langs = {}

    file_name = f"repo-{repo_name}.html"
    path = os.path.join(site_dir, file_name)

    topics_txt = ", ".join(topics) if topics else "-"
    langs_txt = ", ".join([f"{k}: {v}" for k, v in langs.items()]) if langs else "-"

    html = f"""<!doctype html>
<html lang="pt-br">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(repo_name)}</title></head>
<body>
  <p><a href="index.html">Voltar</a></p>
  <h1>{esc(repo_name)}</h1>

  <ul>
    <li><b>GitHub:</b> <a href="{esc(repo.get("html_url",""))}" target="_blank">{esc(repo.get("html_url",""))}</a></li>
    <li><b>Descrição:</b> {esc(repo.get("description") or "-")}</li>
    <li><b>Privado:</b> {repo.get("private")}</li>
    <li><b>Default branch:</b> {esc(repo.get("default_branch") or "-")}</li>
    <li><b>Linguagem principal:</b> {esc(repo.get("language") or "-")}</li>
    <li><b>Stars:</b> {repo.get("stargazers_count", 0)}</li>
    <li><b>Forks:</b> {repo.get("forks_count", 0)}</li>
    <li><b>Issues abertas:</b> {repo.get("open_issues_count", 0)}</li>
    <li><b>Criado em:</b> {esc(repo.get("created_at") or "-")}</li>
    <li><b>Atualizado em:</b> {esc(repo.get("updated_at") or "-")}</li>
    <li><b>Topics:</b> {esc(topics_txt)}</li>
    <li><b>Linguagens (bytes):</b> {esc(langs_txt)}</li>
  </ul>
</body>
</html>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    return file_name

def write_index(site_dir, owner, repos):
    now = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    items = []
    for repo in repos:
        repo_name = repo.get("name", "")
        if not repo_name:
            continue
        detail_file = f"repo-{repo_name}.html"
        items.append(
            f"<li><a href='{esc(detail_file)}'>{esc(repo_name)}</a> — "
            f"<a href='{esc(repo.get('html_url',''))}' target='_blank'>GitHub</a></li>"
        )

    html = f"""<!doctype html>
<html lang="pt-br">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Repos — {esc(owner)}</title></head>
<body>
  <h1>Repositórios — {esc(owner)}</h1>
  <p>Gerado em: {esc(now)}</p>
  <ul>
    {''.join(items) if items else '<li>Nenhum repositório encontrado.</li>'}
  </ul>
</body>
</html>
"""
    with open(os.path.join(site_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

def main():
    token = os.getenv("GH_TOKEN", "").strip()
    owner = os.getenv("GH_OWNER", "").strip()
    scope = os.getenv("GH_SCOPE", "user").strip().lower()

    if not token or not owner:
        raise SystemExit("Defina GH_TOKEN e GH_OWNER no workflow/env.")

    site_dir = "site"
    ensure_dir(site_dir)

    repos = fetch_repos(owner, scope, token)

    # gera páginas de detalhe
    for repo in repos:
        write_repo_detail(site_dir, owner, repo)

    # gera index por último
    write_index(site_dir, owner, repos)

    print(f"[OK] Gerado: {site_dir}/index.html com {len(repos)} repositórios.")

if __name__ == "__main__":
    main()
