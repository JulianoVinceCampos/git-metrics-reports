import os
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

API = "https://api.github.com"
PER_PAGE = 100  # máximo permitido pela API

def esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)

def gh_request(url: str, token: str):
    headers = {
        "Authorization": "Bearer {}".format(token),
        "User-Agent": "simple-git-report",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return body, resp.headers
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8")
        except Exception:
            pass
        raise RuntimeError("HTTP {} | {} | {}".format(e.code, url, body[:300])) from e

def gh_get_json(url: str, token: str):
    body, headers = gh_request(url, token)
    return json.loads(body), headers

def parse_link_header(link_header):
    if not link_header:
        return {}
    parts = [p.strip() for p in link_header.split(",")]
    out = {}
    for p in parts:
        if "; " in p:
            url_part, rel_part = p.split("; ", 1)
            link = url_part.strip("<>")
            rel = rel_part.split("=", 1)[1].strip('"')
            out[rel] = link
    return out

def fetch_repos(owner: str, scope: str, token: str):
    scope = (scope or "user").lower()
    if scope == "org":
        url = "{}/orgs/{}/repos?per_page=100&type=all&sort=updated&direction=desc".format(API, owner)
    else:
        url = "{}/users/{}/repos?per_page=100&type=all&sort=updated&direction=desc".format(API, owner)

    data, _ = gh_get_json(url, token)
    if not isinstance(data, list):
        raise RuntimeError("Resposta inesperada ao listar repositórios.")
    return data

def fetch_all_commits(owner: str, repo: str, token: str, default_branch: str):
    commits = []
    page = 1

    while True:
        params = {
            "per_page": PER_PAGE,
            "page": page,
            "sha": default_branch
        }
        url = "{}/repos/{}/{}/commits?{}".format(API, owner, repo, urllib.parse.urlencode(params))
        data, headers = gh_get_json(url, token)

        if not isinstance(data, list):
            raise RuntimeError("Resposta inesperada em commits de {}/{}.".format(owner, repo))

        for c in data:
            commit_obj = (c.get("commit") or {})
            author_obj = (commit_obj.get("author") or {})
            msg = commit_obj.get("message") or ""
            msg_first = msg.split("\n")[0]

            commits.append({
                "sha": c.get("sha"),
                "date": author_obj.get("date"),
                "author": author_obj.get("name"),
                "message": msg_first,
                "html_url": c.get("html_url"),
            })

        links = parse_link_header(headers.get("Link"))
        if "next" in links:
            page += 1
        else:
            break

    return commits

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

def write_repo_page(site_dir: str, owner: str, repo: dict, commits: list):
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

    data_dir = os.path.join(site_dir, "data")
    ensure_dir(data_dir)
    commits_json_name = "{}-commits.json".format(name)
    commits_json_path = os.path.join(data_dir, commits_json_name)
    with open(commits_json_path, "w", encoding="utf-8") as f:
        json.dump(commits, f, ensure_ascii=False, indent=2)

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

    lines.append("<p><b>Total de commits:</b> {}</p>".format(len(commits)))
    lines.append("<p><b>Download commits (JSON):</b> <a href='data/{0}' target='_blank'>{0}</a></p>".format(esc(commits_json_name)))

    # Lista completa (pode ficar grande, mas você pediu sem limitação)
    lines.append("<h2>Commits (todos)</h2>")
    lines.append("<ol>")
    for c in commits:
        sha = esc((c.get("sha") or "")[:8])
        date = esc(c.get("date") or "-")
        author = esc(c.get("author") or "-")
        msg = esc(c.get("message") or "-")
        urlc = esc(c.get("html_url") or "")
        if urlc:
            lines.append("<li><b>{}</b> • {} • {} — <a href='{}' target='_blank'>{}</a></li>".format(sha, date, author, urlc, msg))
        else:
            lines.append("<li><b>{}</b> • {} • {} — {}</li>".format(sha, date, author, msg))
    lines.append("</ol>")

    lines += html_tail()

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def write_index(site_dir: str, owner: str, repos: list, repo_commit_counts: dict):
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
        commits_total = repo_commit_counts.get(name, 0)

        lines.append(
            "<li><a href='{0}.html'>{0}</a> — commits: <b>{2}</b> — <a href='{1}' target='_blank'>GitHub</a></li>".format(
                esc(name),
                esc(html_url),
                commits_total
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
    ensure_dir(os.path.join(site_dir, "data"))

    repos = fetch_repos(owner, scope, token)

    repo_commit_counts = {}

    for repo in repos:
        name = repo.get("name") or ""
        if not name:
            continue

        default_branch = repo.get("default_branch") or "main"
        print("[INFO] {} -> coletando commits (branch: {})".format(name, default_branch))

        commits = fetch_all_commits(owner, name, token, default_branch)
        repo_commit_counts[name] = len(commits)

        write_repo_page(site_dir, owner, repo, commits)

    write_index(site_dir, owner, repos, repo_commit_counts)
    print("[OK] Gerado: {}/index.html".format(site_dir))

if __name__ == "__main__":
    main()
