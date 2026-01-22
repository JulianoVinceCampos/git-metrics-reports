import os
import json
import urllib.request
import urllib.error
from datetime import datetime

API = "https://api.github.com"

def esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)

def gh_get_json(url: str, token: str):
    headers = {
        "Authorization": "Bearer {}".format(token),
        "User-Agent": "simple-git-report",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8")
        except Exception:
            pass
        raise RuntimeError("HTTP {} | {} | {}".format(e.code, url, body[:300])) from e

def fetch_repos(owner: str, scope: str, token: str):
    scope = (scope or "user").lower()
    if scope == "org":
        url = "{}/orgs/{}/repos?per_page=100&type=all&sort=updated&direction=desc".format(API, owner)
    else:
        url = "{}/users/{}/repos?per_page=100&type=all&sort=updated&direction=desc".format(API, owner)

    data = gh_get_json(url, token)
    if not isinstance(data, list):
        raise RuntimeError("Resposta inesperada ao listar repositórios.")
    return data

def html_head(title: str):
    return [
        "<!doctype html>",
        "<html lang='pt-br'>",
        "<head>",
        "<meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<title>{}</title>".format(esc(title)),
        "</head>",
        "<body>",
    ]

def html_tail():
    return ["</body>", "</html>"]

def write_repo_page(site_dir: str, owner: str, repo: dict):
    name = repo.get("name") or "repo"
    path = os.path.join(site_dir, "{}.html".format(name))

    html_url = repo.get("html_url") or ""
    desc = repo.get("description") or "-"
    default_branch = repo.get("default_branch") or "-"
    language = repo.get("language") or "-"
    private = repo.get("private")
    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    issues = repo.get("open_issues_count", 0)
    created = repo.get("created_at") or "-"
    updated = repo.get("updated_at") or "-"

    lines = []
    lines += html_head(name)
    lines.append("<p><a href='index.html'>Voltar</a></p>")
    lines.append("<h1>{}</h1>".format(esc(name)))
    lines.append("<ul>")
    lines.append("<li><b>Owner:</b> {}</li>".format(esc(owner)))
    lines.append("<li><b>GitHub:</b> <a href='{0}' target='_blank'>{0}</a></li>".format(esc(html_url)))
    lines.append("<li><b>Descrição:</b> {}</li>".format(esc(desc)))
    lines.append("<li><b>Privado:</b> {}</li>".format(private))
    lines.append("<li><b>Branch padrão:</b> {}</li>".format(esc(default_branch)))
    lines.append("<li><b>Linguagem principal:</b> {}</li>".format(esc(language)))
    lines.append("<li><b>Stars:</b> {}</li>".format(stars))
    lines.append("<li><b>Forks:</b> {}</li>".format(forks))
    lines.append("<li><b>Issues abertas:</b> {}</li>".format(issues))
    lines.append("<li><b>Criado em:</b> {}</li>".format(esc(created)))
    lines.append("<li><b>Atualizado em:</b> {}</li>".format(esc(updated)))
    lines.append("</ul>")
    lines += html_tail()

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def write_index(site_dir: str, owner: str, repos: list):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = []
    lines += html_head("Repos — {}".format(owner))
    lines.append("<h1>Repositórios — {}</h1>".format(esc(owner)))
    lines.append("<p>Gerado em: {}</p>".format(esc(now)))
    lines.append("<ul>")

    count = 0
    for r in repos:
        name = r.get("name")
        if not name:
            continue
        html_url = r.get("html_url") or ""
        lines.append(
            "<li><a href='{0}.html'>{0}</a> — <a href='{1}' target='_blank'>GitHub</a></li>".format(
                esc(name),
                esc(html_url),
            )
        )
        count += 1

    if count == 0:
        lines.append("<li>Nenhum repositório encontrado.</li>")

    lines.append("</ul>")
    lines += html_tail()

    with open(os.path.join(site_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def main():
    token = (os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN") or "").strip()
    owner = os.getenv("GH_OWNER", "").strip()
    scope = (os.getenv("GH_SCOPE") or "user").strip().lower()

    if not token:
        raise SystemExit("Token não encontrado. Defina GH_TOKEN ou use GITHUB_TOKEN.")
    if not owner:
        raise SystemExit("Owner não encontrado. Defina GH_OWNER.")

    site_dir = "site"
    ensure_dir(site_dir)

    repos = fetch_repos(owner, scope, token)

    for repo in repos:
        write_repo_page(site_dir, owner, repo)

    write_index(site_dir, owner, repos)

    print("[OK] Gerado: {}/index.html ({} repos, até 100).".format(site_dir, len(repos)))

if __name__ == "__main__":
    main()
