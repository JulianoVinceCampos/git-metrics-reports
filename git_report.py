import os
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

API = "https://api.github.com"
PER_PAGE = 100  # máximo da API

CSS = (
    "body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;"
    "background:#f8fafc;color:#0f172a;margin:0;padding:24px;}"
    ".container{max-width:1200px;margin:0 auto;}"
    ".top{display:flex;justify-content:space-between;align-items:flex-end;gap:12px;"
    "border-bottom:1px solid #e2e8f0;padding-bottom:12px;margin-bottom:18px;}"
    "h1{font-size:22px;margin:0;letter-spacing:-.2px;}"
    "h2{font-size:16px;margin:18px 0 10px 0;}"
    ".muted{color:#64748b;font-size:13px;}"
    ".card{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:14px 16px;margin:12px 0;}"
    ".kpi{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0 6px 0;}"
    ".pill{background:#0ea5e9;color:#fff;border-radius:999px;padding:6px 10px;font-size:12px;font-weight:700;}"
    ".pill2{background:#10b981;}"
    ".btn{display:inline-block;text-decoration:none;font-weight:700;font-size:13px;"
    "padding:8px 10px;border-radius:10px;border:1px solid #bfdbfe;background:#eff6ff;color:#2563eb;}"
    ".btn:hover{background:#dbeafe;}"
    ".btn2{border:1px solid #bbf7d0;background:#f0fdf4;color:#166534;}"
    ".btn2:hover{background:#dcfce7;}"
    "a{color:#2563eb;}"
    "ul{margin:10px 0 0 18px;}"
    "li{margin:6px 0;}"
    "ol{margin:10px 0 0 18px;}"
    "code{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;font-size:12px;}"
    ".row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;}"
    ".spacer{height:8px;}"
)

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
        params = {"per_page": PER_PAGE, "page": page, "sha": default_branch}
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
        "<style>{}</style>".format(CSS),
        "</head>",
        "<body>",
        "<div class='container'>",
    ]

def html_tail():
    return ["</div>", "</body>", "</html>"]

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

    lines.append("<div class='top'>")
    lines.append("<div>")
    lines.append("<h1>{}</h1>".format(esc(name)))
    lines.append("<div class='muted'>{}/{} • branch padrão: <b>{}</b></div>".format(esc(owner), esc(name), esc(default_branch)))
    lines.append("</div>")
    lines.append("<div class='row'>")
    lines.append("<a class='btn' href='index.html'>Voltar</a>")
    lines.append("<a class='btn btn2' href='{}' target='_blank'>Abrir no GitHub</a>".format(esc(html_url)))
    lines.append("</div>")
    lines.append("</div>")

    lines.append("<div class='kpi'>")
    lines.append("<span class='pill'>Commits: {}</span>".format(len(commits)))
    lines.append("<span class='pill pill2'>Stars: {}</span>".format(stars))
    lines.append("<span class='pill pill2'>Forks: {}</span>".format(forks))
    lines.append("<span class='pill pill2'>Issues: {}</span>".format(issues))
    lines.append("</div>")

    lines.append("<div class='card'>")
    lines.append("<div class='muted'><b>Descrição:</b> {}</div>".format(esc(desc)))
    lines.append("<div class='spacer'></div>")
    lines.append("<ul>")
    lines.append("<li><b>Privado:</b> {}</li>".format(private))
    lines.append("<li><b>Linguagem principal:</b> {}</li>".format(esc(language)))
    lines.append("<li><b>Criado em:</b> {}</li>".format(esc(created)))
    lines.append("<li><b>Atualizado em:</b> {}</li>".format(esc(updated)))
    lines.append("<li><b>Download commits (JSON):</b> <a href='data/{0}' target='_blank'>{0}</a></li>".format(esc(commits_json_name)))
    lines.append("</ul>")
    lines.append("</div>")

    lines.append("<div class='card'>")
    lines.append("<h2>Commits (todos)</h2>")
    lines.append("<ol>")
    for c in commits:
        sha8 = esc((c.get("sha") or "")[:8])
        date = esc(c.get("date") or "-")
        author = esc(c.get("author") or "-")
        msg = esc(c.get("message") or "-")
        urlc = esc(c.get("html_url") or "")
        if urlc:
            lines.append(
                "<li><code>{}</code> • {} • {} — <a href='{}' target='_blank'>{}</a></li>".format(
                    sha8, date, author, urlc, msg
                )
            )
        else:
            lines.append("<li><code>{}</code> • {} • {} — {}</li>".format(sha8, date, author, msg))
    lines.append("</ol>")
    lines.append("</div>")

    lines.append("<div class='muted'>Gerado em: {} UTC</div>".format(esc(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))))

    lines += html_tail()

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def write_index(site_dir: str, owner: str, repos: list, repo_commit_counts: dict):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = []
    lines += html_head("Repos — {}".format(owner))

    lines.append("<div class='top'>")
    lines.append("<div>")
    lines.append("<h1>Dashboard Executivo — Repositórios</h1>")
    lines.append("<div class='muted'>Owner: <b>{}</b> • Gerado em: <b>{}</b></div>".format(esc(owner), esc(now)))
    lines.append("</div>")
    lines.append("<div class='kpi'>")
    lines.append("<span class='pill'>Total de repos: {}</span>".format(len(repos)))
    lines.append("</div>")
    lines.append("</div>")

    lines.append("<div class='card'>")
    lines.append("<h2>Lista de repositórios</h2>")
    lines.append("<ul>")

    count = 0
    for r in repos:
        name = r.get("name")
        if not name:
            continue
        html_url = r.get("html_url") or ""
        commits_total = repo_commit_counts.get(name, 0)

        lines.append(
            "<li><a class='btn' href='{0}.html'>{0}</a> "
            "<span class='muted'>commits:</span> <b>{2}</b> "
            "<span class='muted'>•</span> <a href='{1}' target='_blank'>GitHub</a></li>".format(
                esc(name), esc(html_url), commits_total
            )
        )
        count += 1

    if count == 0:
        lines.append("<li>Nenhum repositório encontrado.</li>")

    lines.append("</ul>")
    lines.append("</div>")

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
