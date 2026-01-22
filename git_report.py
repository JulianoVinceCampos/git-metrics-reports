import os
import json
import math
import datetime as dt
import urllib.request
import urllib.parse
import urllib.error

API = "https://api.github.com"

# ======= CONFIG PADRÃO (pode alterar por env) =======
DEFAULT_GENERAL_DAYS = int(os.getenv("GH_GENERAL_DAYS", "365"))   # Relatório Geral = últimos 365 dias
DISPLAY_COMMITS_LIMIT = int(os.getenv("GH_DISPLAY_LIMIT", "500")) # commits exibidos por página html
PER_PAGE = 100

def gh_get(path, token, params=None, accept_preview_topics=False):
    url = f"{API}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "git-metrics-reports",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if accept_preview_topics:
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

        msg = f"HTTP {e.code} ao acessar {path}"
        if e.code in (401, 403):
            msg += " (token sem permissão / rate limit / acesso negado)"
        if body:
            msg += f" | body: {body[:400]}"
        raise RuntimeError(msg) from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Erro de rede ao acessar {path}: {e}") from e

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

def paginate(path, token, params=None, per_page=PER_PAGE):
    page = 1
    all_items = []
    while True:
        p = dict(params or {})
        p["per_page"] = per_page
        p["page"] = page
        data, headers = gh_get(path, token, p)
        if not isinstance(data, list):
            raise RuntimeError(f"Expected list, got: {type(data)} for {path}")
        all_items.extend(data)
        links = parse_link_header(headers.get("Link"))
        if "next" in links:
            page += 1
        else:
            break
    return all_items

def iso(dt_obj):
    return dt_obj.replace(microsecond=0).isoformat() + "Z"

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

def sanitize_repo_name(name: str) -> str:
    return name.strip().lstrip("-").strip()

def fetch_repos(owner, scope, token):
    if scope == "org":
        path = f"/orgs/{owner}/repos"
        params = {"type": "all", "sort": "updated", "direction": "desc"}
    else:
        path = f"/users/{owner}/repos"
        params = {"type": "all", "sort": "updated", "direction": "desc"}
    return paginate(path, token, params=params)

def fetch_repo_topics(owner, repo, token):
    data, _ = gh_get(f"/repos/{owner}/{repo}/topics", token, accept_preview_topics=True)
    return data.get("names", [])

def fetch_repo_languages(owner, repo, token):
    data, _ = gh_get(f"/repos/{owner}/{repo}/languages", token)
    return data  # dict {lang: bytes}

def fetch_commits(owner, repo, token, since=None):
    params = {}
    if since:
        params["since"] = since
    commits = paginate(f"/repos/{owner}/{repo}/commits", token, params=params, per_page=PER_PAGE)

    out = []
    for c in commits:
        commit = c.get("commit", {}) or {}
        author = commit.get("author", {}) or {}
        committer = commit.get("committer", {}) or {}
        out.append({
            "sha": c.get("sha"),
            "message": (commit.get("message") or "").split("\n")[0],
            "author_name": author.get("name"),
            "author_email": author.get("email"),
            "author_date": author.get("date"),
            "committer_name": committer.get("name"),
            "committer_date": committer.get("date"),
            "html_url": c.get("html_url"),
        })
    return out

def html_escape(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

CSS = """
<style>
  :root { --primary:#0f172a; --accent:#3b82f6; --bg:#f8fafc; --card:#ffffff; --muted:#64748b; }
  body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; background:var(--bg); color:var(--primary); margin:0; padding:32px; }
  .container { max-width:1200px; margin:0 auto; }
  .header { display:flex; justify-content:space-between; align-items:flex-end; gap:16px; border-bottom:1px solid #e2e8f0; padding-bottom:16px; margin-bottom:24px; }
  h1 { margin:0; font-size:22px; }
  .muted { color:var(--muted); font-size:13px; }
  .grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(320px, 1fr)); gap:16px; }
  .card { background:var(--card); border:1px solid #e2e8f0; border-radius:14px; padding:16px; }
  .kpi { display:flex; gap:16px; flex-wrap:wrap; margin:16px 0 24px; }
  .kpi .box { background:var(--card); border:1px solid #e2e8f0; border-radius:14px; padding:14px 16px; min-width:220px; }
  .kpi .label { font-size:12px; color:var(--muted); text-transform:uppercase; }
  .kpi .value { font-size:22px; font-weight:800; margin-top:6px; }
  a.btn { display:inline-block; padding:8px 10px; border-radius:10px; text-decoration:none; font-weight:650; font-size:13px; border:1px solid #bfdbfe; background:#eff6ff; color:#2563eb; }
  a.btn2 { border:1px solid #bbf7d0; background:#f0fdf4; color:#166534; }
  table { width:100%; border-collapse:collapse; margin-top:10px; }
  th, td { text-align:left; border-bottom:1px solid #e2e8f0; padding:8px; font-size:13px; vertical-align:top; }
  th { color:var(--muted); font-weight:700; }
  code { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size:12px; }
  .warn { background:#fff7ed; border:1px solid #fed7aa; padding:10px 12px; border-radius:12px; color:#9a3412; font-size:13px; margin:12px 0; }
</style>
"""

def write_repo_page(site_dir, owner, repo_name, repo_meta, commits_all, commits_90d, general_days):
    repo_file = os.path.join(site_dir, f"{repo_name}.html")
    repo90_file = os.path.join(site_dir, f"{repo_name}_90d.html")

    def page(title, commits, note=None):
        topics = repo_meta.get("topics", [])
        langs = repo_meta.get("languages", {})
        total_lang_bytes = sum(langs.values()) or 1
        langs_top = sorted(langs.items(), key=lambda x: x[1], reverse=True)[:8]

        rows = []
        for c in commits[:DISPLAY_COMMITS_LIMIT]:
            rows.append(
                "<tr>"
                f"<td><code>{html_escape(c['sha'][:8])}</code></td>"
                f"<td>{html_escape(c['message'])}</td>"
                f"<td>{html_escape(c.get('author_name') or '')}</td>"
                f"<td>{html_escape(c.get('author_date') or '')}</td>"
                f"<td><a href='{html_escape(c.get('html_url') or '#')}' target='_blank'>ver</a></td>"
                "</tr>"
            )

        topics_html = ", ".join(html_escape(t) for t in topics) if topics else "-"
        langs_html = ", ".join(
            f"{html_escape(k)} ({math.floor((v/total_lang_bytes)*100)}%)"
            for k, v in langs_top
        ) if langs else "-"

        warn_html = f"<div class='warn'>{html_escape(note)}</div>" if note else ""

        return f"""<!doctype html>
<html lang="pt-br">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html_escape(title)}</title>{CSS}</head>
<body><div class="container">
  <div class="header">
    <div>
      <h1>{html_escape(title)}</h1>
      <div class="muted">{html_escape(owner)}/{html_escape(repo_name)} • Default branch: <b>{html_escape(repo_meta.get('default_branch',''))}</b></div>
    </div>
    <div><a class="btn" href="index.html">Voltar</a></div>
  </div>

  {warn_html}

  <div class="kpi">
    <div class="box"><div class="label">Commits capturados</div><div class="value">{len(commits)}</div></div>
    <div class="box"><div class="label">Stars / Forks</div><div class="value">{repo_meta.get('stargazers_count',0)} / {repo_meta.get('forks_count',0)}</div></div>
    <div class="box"><div class="label">Issues abertas</div><div class="value">{repo_meta.get('open_issues_count',0)}</div></div>
  </div>

  <div class="card">
    <div class="muted"><b>Descrição:</b> {html_escape(repo_meta.get("description") or "-")}</div>
    <div class="muted" style="margin-top:8px;"><b>Topics:</b> {topics_html}</div>
    <div class="muted" style="margin-top:8px;"><b>Linguagens (top):</b> {langs_html}</div>
    <div class="muted" style="margin-top:8px;"><b>Criado em:</b> {html_escape(repo_meta.get("created_at",""))} • <b>Atualizado em:</b> {html_escape(repo_meta.get("updated_at",""))}</div>
    <div class="muted" style="margin-top:8px;"><b>URL:</b> <a href="{html_escape(repo_meta.get("html_url",""))}" target="_blank">abrir no GitHub</a></div>
  </div>

  <div class="card" style="margin-top:16px;">
    <b>Commits (limite de exibição: {DISPLAY_COMMITS_LIMIT})</b>
    <table>
      <thead><tr><th>SHA</th><th>Mensagem</th><th>Autor</th><th>Data</th><th>Link</th></tr></thead>
      <tbody>
        {''.join(rows) if rows else '<tr><td colspan="5">Sem commits no período.</td></tr>'}
      </tbody>
    </table>
  </div>

  <div class="muted" style="margin-top:18px;">Gerado em {dt.datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')} UTC</div>
</div></body></html>"""

    # Geral (últimos N dias)
    note_general = f"Observação: este relatório geral foi limitado aos últimos {general_days} dias para evitar excesso de tempo/rate limit no GitHub Actions."
    with open(repo_file, "w", encoding="utf-8") as f:
        f.write(page(f"Relatório Geral • {owner}/{repo_name}", commits_all, note=note_general))

    with open(repo90_file, "w", encoding="utf-8") as f:
        f.write(page(f"Últimos 90 dias • {owner}/{repo_name}", commits_90d))

def write_index(site_dir, owner, repos_compiled):
    now = dt.datetime.utcnow()
    cards = []
    for r in repos_compiled:
        name = r["name"]
        cards.append(f"""
        <div class="card">
          <div style="font-weight:800; font-size:16px; margin-bottom:6px;">{html_escape(name)}</div>
          <div class="muted">{html_escape(r.get("description") or "-")}</div>
          <div class="muted" style="margin-top:8px;">
            Commits (90d): <b>{r["commits_90d"]}</b> • Geral: <b>{r["commits_all"]}</b>
          </div>
          <div style="margin-top:12px; display:flex; gap:10px; flex-wrap:wrap;">
            <a class="btn" href="{html_escape(name)}.html">Relatório Geral</a>
            <a class="btn btn2" href="{html_escape(name)}_90d.html">Últimos 90 Dias</a>
            <a class="btn" href="{html_escape(r.get("html_url",""))}" target="_blank">Repo</a>
          </div>
        </div>
        """)

    html = f"""<!doctype html>
<html lang="pt-br">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Engenharia | Dashboard Executivo</title>{CSS}</head>
<body><div class="container">
  <div class="header">
    <div>
      <h1>Dashboard Executivo de Engenharia</h1>
      <div class="muted">Fonte: GitHub API • Owner: <b>{html_escape(owner)}</b></div>
    </div>
    <div class="muted">Atualizado: <b>{now.strftime('%d/%m/%Y %H:%M:%S')} UTC</b></div>
  </div>

  <div class="kpi">
    <div class="box"><div class="label">Total de Projetos</div><div class="value">{len(repos_compiled)}</div></div>
  </div>

  <div class="grid">
    {''.join(cards) if cards else '<div class="card">Nenhum repositório encontrado.</div>'}
  </div>

  <div class="muted" style="margin-top:18px;">Gerado automaticamente via GitHub Actions.</div>
</div></body></html>"""

    with open(os.path.join(site_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

def main():
    token = os.getenv("GH_TOKEN", "").strip()
    owner = os.getenv("GH_OWNER", "").strip()
    scope = os.getenv("GH_SCOPE", "user").strip().lower()
    general_days = int(os.getenv("GH_GENERAL_DAYS", str(DEFAULT_GENERAL_DAYS)))

    if not token or not owner:
        raise SystemExit("Defina GH_TOKEN e GH_OWNER no workflow/env.")

    site_dir = "site"
    ensure_dir(site_dir)
    ensure_dir(os.path.join(site_dir, "data"))

    print(f"[INFO] Owner={owner} scope={scope} general_days={general_days}")

    try:
        repos = fetch_repos(owner, scope, token)
    except Exception as e:
        raise SystemExit(f"[FATAL] Falha ao listar repositórios: {e}")

    now = dt.datetime.utcnow()
    since_90d = iso(now - dt.timedelta(days=90))
    since_general = iso(now - dt.timedelta(days=general_days))

    compiled = []
    for r in repos:
        repo_name = sanitize_repo_name(r.get("name", ""))
        if not repo_name:
            continue

        print(f"[INFO] Processing repo: {repo_name}")

        try:
            topics = fetch_repo_topics(owner, repo_name, token)
            languages = fetch_repo_languages(owner, repo_name, token)

            # Geral limitado (evita bomba)
            commits_all = fetch_commits(owner, repo_name, token, since=since_general)
            commits_90d = fetch_commits(owner, repo_name, token, since=since_90d)

            repo_meta = dict(r)
            repo_meta["topics"] = topics
            repo_meta["languages"] = languages

            payload = {
                "repo": repo_meta,
                "commits_general_days": general_days,
                "commits_all": commits_all,
                "commits_90d": commits_90d,
                "generated_at_utc": iso(dt.datetime.utcnow()),
            }
            with open(os.path.join(site_dir, "data", f"{repo_name}.json"), "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            write_repo_page(site_dir, owner, repo_name, repo_meta, commits_all, commits_90d, general_days)

            compiled.append({
                "name": repo_name,
                "description": repo_meta.get("description"),
                "html_url": repo_meta.get("html_url"),
                "commits_all": len(commits_all),
                "commits_90d": len(commits_90d),
            })

        except Exception as e:
            # não derruba o job; registra no index como erro
            print(f"[WARN] Repo {repo_name} falhou: {e}")
            compiled.append({
                "name": repo_name,
                "description": (r.get("description") or "") + " (ERRO ao coletar dados)",
                "html_url": r.get("html_url"),
                "commits_all": 0,
                "commits_90d": 0,
            })

    write_index(site_dir, owner, compiled)
    print("[INFO] Done.")

if __name__ == "__main__":
    main()
