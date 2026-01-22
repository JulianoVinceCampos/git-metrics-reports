import subprocess
import sys
import os
import argparse
from collections import Counter
from datetime import datetime, date

# -----------------------------
# Helpers
# -----------------------------

NL = "\n"

def push(lines, *parts):
    # Append seguro. Junta e adiciona ao buffer.
    lines.append("".join(parts))

def join_lines(*rows):
    # Cria blocos multi-linha sem usar aspas triplas.
    return NL.join(rows)

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
        # Se não houver commits, o git log retorna erro. Tratamos como vazio.
        return ""
    return r.stdout

def esc(s: str) -> str:
    return (str(s) or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def fmt_int(n: int) -> str:
    try:
        return f"{int(n):,}".replace(",", ".")
    except Exception:
        return "0"

def month_label(ym: str) -> str:
    # "YYYY-MM" -> "MM/YYYY"
    try:
        y, m = ym.split("-")
        return f"{m}/{y}"
    except Exception:
        return ym

def parse_iso_date(s: str):
    try:
        y, m, d = s.split("-")
        return date(int(y), int(m), int(d))
    except Exception:
        return None

def days_between(a: str, b: str) -> int:
    da = parse_iso_date(a)
    db = parse_iso_date(b)
    if not da or not db:
        return 0
    return abs((db - da).days)

def svg_frame_open(width, height, title):
    return join_lines(
        '<div class="chart-wrap">',
        f'  <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{esc(title)}">',
        f'    <rect x="0" y="0" width="{width}" height="{height}" rx="14" ry="14" fill="#ffffff" stroke="#e5e7eb"/>'
    )

def svg_frame_close():
    return join_lines(
        "  </svg>",
        "</div>"
    )

# -----------------------------
# Charts (Removidas docstrings com aspas triplas)
# -----------------------------

def svg_bar_chart(items, width=980, bar_h=22, gap=10, left_pad=280, right_pad=28, top_pad=26, bottom_pad=22, title=""):
    # items: lista de tuplas (label, valor)
    if not items:
        return "<div class='muted'>Sem dados para exibir.</div>"

    maxv = max(v for _, v in items) or 1
    height = top_pad + bottom_pad + len(items) * (bar_h + gap)
    usable_w = width - left_pad - right_pad

    lines = []
    push(lines, f"<div class='card-title'>{esc(title)}</div>")
    push(lines, svg_frame_open(width, height, title))

    y = top_pad
    for label, v in items:
        w = int((v / maxv) * usable_w) if maxv else 0
        safe_label = esc(label)

        push(lines, f'<text x="{left_pad-12}" y="{y+bar_h-6}" font-size="12" text-anchor="end" fill="#0f172a">{safe_label}</text>')
        push(lines, f'<rect x="{left_pad}" y="{y}" width="{usable_w}" height="{bar_h}" rx="8" ry="8" fill="#f1f5f9" />')
        push(lines, f'<rect x="{left_pad}" y="{y}" width="{w}" height="{bar_h}" rx="8" ry="8" fill="#2563eb" />')
        push(lines, f'<text x="{left_pad + w + 10}" y="{y+bar_h-6}" font-size="12" fill="#0f172a">{fmt_int(v)}</text>')
        y += bar_h + gap

    push(lines, svg_frame_close())
    return NL.join(lines)

def svg_line_chart(series, width=980, height=300, left_pad=64, right_pad=26, top_pad=26, bottom_pad=52, title=""):
    # series: lista de tuplas (x_label, valor)
    if not series:
        return "<div class='muted'>Sem dados históricos.</div>"

    maxv = max(v for _, v in series) or 1
    minv = 0
    usable_w = width - left_pad - right_pad
    usable_h = height - top_pad - bottom_pad

    def x_pos(i):
        if len(series) <= 1: return left_pad + usable_w // 2
        return left_pad + int(i * (usable_w / (len(series) - 1)))

    def y_pos(v):
        denom = (maxv - minv) if maxv != minv else 1
        return top_pad + int((maxv - v) * (usable_h / denom))

    pts = [(x_pos(i), y_pos(v)) for i, (_, v) in enumerate(series)]
    path = "M " + " L ".join(f"{x},{y}" for x, y in pts)

    lines = []
    push(lines, f"<div class='card-title'>{esc(title)}</div>")
    push(lines, svg_frame_open(width, height, title))

    for t in range(0, 6):
        v = int(maxv * (t / 5))
        y = y_pos(v)
        push(lines, f'<line x1="{left_pad}" y1="{y}" x2="{left_pad+usable_w}" y2="{y}" stroke="#e5e7eb" />')
        push(lines, f'<text x="{left_pad-10}" y="{y+4}" font-size="11" text-anchor="end" fill="#475569">{fmt_int(v)}</text>')

    push(lines, f'<line x1="{left_pad}" y1="{top_pad+usable_h}" x2="{left_pad+usable_w}" y2="{top_pad+usable_h}" stroke="#cbd5e1" />')
    push(lines, f'<path d="{path}" fill="none" stroke="#2563eb" stroke-width="3" />')

    for (x, y), (_, v) in zip(pts, series):
        push(lines, f'<circle cx="{x}" cy="{y}" r="4" fill="#2563eb" />')

    step = max(1, len(series) // 6)
    for i, (xl, _) in enumerate(series):
        if i % step == 0 or i == len(series) - 1:
            x = x_pos(i)
            push(lines, f'<text x="{x}" y="{top_pad+usable_h+26}" font-size="11" text-anchor="middle" fill="#475569">{esc(month_label(xl))}</text>')

    push(lines, svg_frame_close())
    return NL.join(lines)

# -----------------------------
# Main report
# -----------------------------

def build_css():
    return join_lines(
        "<style>",
        ":root{--bg:#f6f8fa;--card:#ffffff;--text:#0f172a;--muted:#475569;--border:#e5e7eb;--blue:#2563eb;--soft:#f1f5f9;}",
        "body{font-family:ui-sans-serif,system-ui,sans-serif;margin:0;background:var(--bg);color:var(--text);}",
        ".wrap{max-width:1100px;margin:0 auto;padding:28px}",
        ".top{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;margin-bottom:14px;flex-wrap:wrap}",
        "h1{margin:0;font-size:28px;letter-spacing:-0.02em}",
        ".subtitle{color:var(--muted);margin:6px 0 0 0}",
        ".meta{color:#64748b;font-size:12.5px}",
        ".grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:14px}",
        "@media (max-width:980px){.grid{grid-template-columns:repeat(2,1fr);}}",
        "@media (max-width:520px){.grid{grid-template-columns:1fr;}}",
        ".kpi{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:14px;box-shadow:0 1px 0 rgba(15,23,42,.04)}",
        ".kpi .v{font-size:26px;font-weight:800;letter-spacing:-0.02em}",
        ".kpi .l{color:var(--muted);margin-top:4px}",
        ".card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:16px;margin:14px 0;box-shadow:0 1px 0 rgba(15,23,42,.04)}",
        ".card-title{font-weight:800;margin:0 0 10px 0}",
        ".muted{color:var(--muted)}",
        ".pill{display:inline-flex;align-items:center;gap:8px;background:var(--soft);color:#1e293b;border:1px solid #e2e8f0;padding:6px 10px;border-radius:999px;font-size:12px}",
        ".row{display:flex;gap:10px;flex-wrap:wrap;margin-top:10px}",
        ".divider{height:1px;background:var(--border);margin:12px 0}",
        ".chart-wrap{overflow:auto;padding-bottom:2px}",
        ".note li{margin:6px 0}",
        "a{color:var(--blue);text-decoration:none}",
        ".footer{margin:18px 0 0 0;color:#64748b;font-size:12.5px}",
        "</style>"
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", default=None)
    parser.add_argument("--out", default="relatorio_git.html")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--title", default="Relatório de Atividade Git")
    args = parser.parse_args()

    repo_abs = os.path.abspath(args.repo)
    git_args = ["log", "--date=short", "--pretty=format:%H\t%an\t%ae\t%ad", "--numstat"]
    if args.since:
        git_args.insert(1, f"--since={args.since}")

    output_raw = run_git(git_args, cwd=repo_abs)
    if not output_raw:
        print("Nenhum commit encontrado.")
        return

    raw = output_raw.splitlines()
    commits = []
    current = None

    for line in raw:
        parts = line.split("\t")
        if len(parts) >= 4 and len(parts[0]) >= 7:
            current = {"hash": parts[0], "author": parts[1].strip(), "email": parts[2].strip(), "date": parts[3].strip(), "add": 0, "del": 0}
            commits.append(current)
        elif current and line.strip() and "\t" in line:
            stat_parts = line.split("\t")
            if len(stat_parts) >= 2:
                if stat_parts[0].isdigit(): current["add"] += int(stat_parts[0])
                if stat_parts[1].isdigit(): current["del"] += int(stat_parts[1])

    by_author_commits = Counter()
    by_author_add = Counter()
    by_author_del = Counter()
    by_month = Counter()

    for c in commits:
        name = c["author"]
        by_author_commits[name] += 1
        by_author_add[name] += c["add"]
        by_author_del[name] += c["del"]
        by_month[c["date"][:7]] += 1

    month_series = sorted(by_month.items(), key=lambda x: x[0])
    total_commits = len(commits)
    total_add = sum(c["add"] for c in commits)
    total_del = sum(c["del"] for c in commits)
    
    gen_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = []
    push(html, "<!doctype html><html lang='pt-br'><head><meta charset='utf-8'>")
    push(html, "<meta name='viewport' content='width=device-width, initial-scale=1'>")
    push(html, f"<title>{esc(args.title)}</title>{build_css()}</head><body>")
    push(html, "<div class='wrap'>")

    # Header
    push(html, "<div class='top'>")
    push(html, f"<div><h1>{esc(args.title)}</h1><p class='subtitle'>Relatório gerado automaticamente via CI.</p></div>")
    push(html, f"<div class='meta'>Gerado em: {esc(gen_at)}</div>")
    push(html, "</div>")

    # KPIs
    push(html, "<div class='grid'>")
    push(html, f"<div class='kpi'><div class='v'>{fmt_int(total_commits)}</div><div class='l'>Commits</div></div>")
    push(html, f"<div class='kpi'><div class='v'>{fmt_int(len(by_author_commits))}</div><div class='l'>Autores</div></div>")
    push(html, f"<div class='kpi'><div class='v'>{fmt_int(total_add)}</div><div class='l'>Linhas Adicionadas</div></div>")
    push(html, f"<div class='kpi'><div class='v'>{fmt_int(total_del)}</div><div class='l'>Linhas Removidas</div></div>")
    push(html, "</div>")

    # Charts
    push(html, f"<div class='card'>{svg_line_chart(month_series, title='Atividade Mensal')}</div>")
    push(html, f"<div class='card'>{svg_bar_chart(by_author_commits.most_common(12), title='Top 12 Autores (Commits)')}</div>")
    push(html, f"<div class='card'>{svg_bar_chart(by_author_add.most_common(12), title='Top 12 Autores (Linhas Adicionadas)')}</div>")

    # Footer
    push(html, "<div class='card note'><div class='card-title'>Dica</div>")
    push(html, "<div class='muted'>Use arquivos <b>.mailmap</b> no repositório para mesclar autores com múltiplos emails.</div></div>")
    push(html, "<div class='footer'>Git Metrics Report</div>")
    push(html, "</div></body></html>")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(NL.join(html))
    print(f"Sucesso: {args.out}")

if __name__ == "__main__":
    main()
