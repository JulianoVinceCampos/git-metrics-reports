import subprocess, sys, os
from collections import defaultdict, Counter
from datetime import datetime

def run_git(args, cwd="."):
    r = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    if r.returncode != 0:
        raise SystemExit(r.stderr.strip() or "Erro ao executar git.")
    return r.stdout

def svg_bar_chart(items, width=900, bar_h=22, gap=10, left_pad=260, right_pad=20, top_pad=20, bottom_pad=20, title=""):
    if not items:
        return "<p>Sem dados.</p>"

    maxv = max(v for _, v in items) or 1
    height = top_pad + bottom_pad + len(items) * (bar_h + gap)

    lines = []
    lines.append(f'<h3>{title}</h3>')
    lines.append(f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">')
    lines.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff" />')

    y = top_pad
    usable_w = width - left_pad - right_pad

    for label, v in items:
        w = int((v / maxv) * usable_w)
        safe_label = (label or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        lines.append(f'<text x="{left_pad-10}" y="{y+bar_h-6}" font-size="12" text-anchor="end" fill="#111">{safe_label}</text>')
        lines.append(f'<rect x="{left_pad}" y="{y}" width="{w}" height="{bar_h}" rx="6" ry="6" fill="#2f6feb" />')
        lines.append(f'<text x="{left_pad + w + 8}" y="{y+bar_h-6}" font-size="12" fill="#111">{v}</text>')
        y += bar_h + gap

    lines.append("</svg>")
    return "\n".join(lines)

def svg_line_chart(series, width=900, height=260, left_pad=60, right_pad=20, top_pad=20, bottom_pad=40, title=""):
    if not series:
        return "<p>Sem dados.</p>"

    maxv = max(v for _, v in series) or 1
    minv = 0
    usable_w = width - left_pad - right_pad
    usable_h = height - top_pad - bottom_pad

    def x_pos(i):
        if len(series) == 1:
            return left_pad + usable_w//2
        return left_pad + int(i * (usable_w / (len(series)-1)))

    def y_pos(v):
        return top_pad + int((maxv - v) * (usable_h / (maxv - minv if maxv != minv else 1)))

    pts = [(x_pos(i), y_pos(v)) for i, (_, v) in enumerate(series)]
    path = "M " + " L ".join(f"{x},{y}" for x,y in pts)

    lines = []
    lines.append(f'<h3>{title}</h3>')
    lines.append(f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">')
    lines.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff" />')

    lines.append(f'<line x1="{left_pad}" y1="{top_pad}" x2="{left_pad}" y2="{top_pad+usable_h}" stroke="#333" />')
    lines.append(f'<line x1="{left_pad}" y1="{top_pad+usable_h}" x2="{left_pad+usable_w}" y2="{top_pad+usable_h}" stroke="#333" />')

    for t in range(0, 6):
        v = int(maxv * (t/5))
        y = y_pos(v)
        lines.append(f'<line x1="{left_pad-5}" y1="{y}" x2="{left_pad}" y2="{y}" stroke="#333" />')
        lines.append(f'<text x="{left_pad-10}" y="{y+4}" font-size="11" text-anchor="end" fill="#111">{v}</text>')

    lines.append(f'<path d="{path}" fill="none" stroke="#2f6feb" stroke-width="3" />')

    for (x,y), (_, v) in zip(pts, series):
        lines.append(f'<circle cx="{x}" cy="{y}" r="4" fill="#2f6feb" />')

    step = max(1, len(series)//6)
    for i, (xl, _) in enumerate(series):
        if i % step != 0 and i != len(series)-1:
            continue
        x = x_pos(i)
        safe = xl.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        lines.append(f'<text x="{x}" y="{top_pad+usable_h+22}" font-size="11" text-anchor="middle" fill="#111">{safe}</text>')

    lines.append("</svg>")
    return "\n".join(lines)

def main():
    since = None
    out = "relatorio_git.html"
    repo = "."

    if "--since" in sys.argv:
        since = sys.argv[sys.argv.index("--since")+1]
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out")+1]
    if "--repo" in sys.argv:
        repo = sys.argv[sys.argv.index("--repo")+1]

    pretty = "%H\t%an\t%ae\t%ad"
    args = ["log", "--date=short", f"--pretty=format:{pretty}", "--numstat"]
    if since:
        args.insert(1, f"--since={since}")

    raw = run_git(args, cwd=repo).splitlines()

    commits = []
    current = None

    for line in raw:
        if "\t" in line and len(line.split("\t")) >= 4 and len(line.split("\t")[0]) >= 7:
            h, an, ae, ad = line.split("\t", 3)
            current = {"hash": h, "author": an.strip(), "email": ae.strip(), "date": ad.strip(), "add": 0, "del": 0}
            commits.append(current)
        elif current and line.strip() and "\t" in line:
            a, d, _ = line.split("\t", 2)
            if a.isdigit(): current["add"] += int(a)
            if d.isdigit(): current["del"] += int(d)

    by_author_commits = Counter()
    by_author_add = Counter()
    by_author_del = Counter()
    by_month = Counter()

    for c in commits:
        key = c["author"]
        by_author_commits[key] += 1
        by_author_add[key] += c["add"]
        by_author_del[key] += c["del"]
        month = c["date"][:7]
        by_month[month] += 1

    top_commits = by_author_commits.most_common(12)
    top_add = by_author_add.most_common(12)
    top_del = by_author_del.most_common(12)

    month_series = sorted(by_month.items(), key=lambda x: x[0])

    total_commits = len(commits)
    total_add = sum(c["add"] for c in commits)
    total_del = sum(c["del"] for c in commits)
    authors = len(by_author_commits)

    gen_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = []
    html.append("<!doctype html><html><head><meta charset='utf-8'>")
    html.append("<meta name='viewport' content='width=device-width, initial-scale=1'>")
    html.append("<title>Relatório Git (Time)</title>")
    html.append("<style>")
    html.append("body{font-family:Arial,Helvetica,sans-serif;margin:24px;color:#111;background:#f6f8fa}")
    html.append(".card{background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:18px;margin:14px 0}")
    html.append(".kpis{display:flex;gap:14px;flex-wrap:wrap}")
    html.append(".kpi{background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:14px;min-width:180px}")
    html.append(".kpi .v{font-size:22px;font-weight:700}")
    html.append("h1{margin:0 0 8px 0}")
    html.append("h3{margin:0 0 10px 0}")
    html.append("small{color:#555}")
    html.append("</style></head><body>")
    html.append("<h1>Relatório de Atividade Git</h1>")
    html.append(f"<small>Gerado em {gen_at}. Fonte: git log local.</small>")

    html.append("<div class='kpis'>")
    html.append(f"<div class='kpi'><div class='v'>{total_commits}</div><div>Commits</div></div>")
    html.append(f"<div class='kpi'><div class='v'>{authors}</div><div>Autores</div></div>")
    html.append(f"<div class='kpi'><div class='v'>{total_add}</div><div>Linhas adicionadas</div></div>")
    html.append(f"<div class='kpi'><div class='v'>{total_del}</div><div>Linhas removidas</div></div>")
    html.append("</div>")

    html.append("<div class='card'>")
    html.append(svg_line_chart(month_series, title="Commits por mês"))
    html.append("</div>")

    html.append("<div class='card'>")
    html.append(svg_bar_chart(top_commits, title="Top autores por commits (Top 12)"))
    html.append("</div>")

    html.append("<div class='card'>")
    html.append(svg_bar_chart(top_add, title="Top autores por linhas adicionadas (Top 12)"))
    html.append("</div>")

    html.append("<div class='card'>")
    html.append(svg_bar_chart(top_del, title="Top autores por linhas removidas (Top 12)"))
    html.append("</div>")

    html.append("<div class='card'>")
    html.append("<h3>Observações rápidas (pra diretoria)</h3>")
    html.append("<ul>")
    html.append("<li>Commits medem atividade, não necessariamente impacto. Use junto com PRs, lead time e entregas.</li>")
    html.append("<li>Se um autor aparece duplicado (nomes/e-mails diferentes), use um .mailmap pra normalizar.</li>")
    html.append("</ul>")
    html.append("</div>")

    html.append("</body></html>")

    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(html))

    print(f"OK: relatório gerado em: {os.path.abspath(out)}")

if __name__ == "__main__":
    main()
