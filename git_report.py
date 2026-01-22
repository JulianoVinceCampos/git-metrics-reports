import subprocess
import os
import argparse
from collections import Counter
from datetime import datetime

# Helpers de Formatação
NL = "\n"
def push(l, *p): l.append("".join(p))
def esc(s): return (str(s) or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
def fmt(n): return f"{int(n):,}".replace(",", ".")

def run_git(args, cwd="."):
    r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else ""

def get_css():
    return """
    <style>
        :root { --primary: #1e293b; --accent: #2563eb; --bg: #f8fafc; --white: #ffffff; --border: #e2e8f0; --text-main: #334155; }
        body { font-family: 'Inter', system-ui, sans-serif; background: var(--bg); color: var(--text-main); margin: 0; padding: 40px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { border-bottom: 2px solid var(--primary); padding-bottom: 20px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: flex-end; }
        h1 { margin: 0; color: var(--primary); font-size: 28px; text-transform: uppercase; letter-spacing: 1px; }
        .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 40px; }
        .kpi-card { background: var(--white); padding: 20px; border-radius: 12px; border: 1px solid var(--border); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        .kpi-val { font-size: 32px; font-weight: 800; color: var(--accent); display: block; }
        .kpi-lab { font-size: 12px; color: #64748b; text-transform: uppercase; font-weight: 600; }
        .card { background: var(--white); padding: 25px; border-radius: 12px; border: 1px solid var(--border); margin-bottom: 30px; }
        .card-title { font-size: 18px; font-weight: 700; margin-bottom: 20px; color: var(--primary); border-left: 4px solid var(--accent); padding-left: 15px; }
        table { width: 100%; border-collapse: collapse; }
        th { text-align: left; padding: 12px; border-bottom: 2px solid var(--border); color: #64748b; font-size: 13px; }
        td { padding: 12px; border-bottom: 1px solid var(--border); font-size: 14px; }
        tr:hover { background: #f1f5f9; }
        .badge { padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; background: #dcfce7; color: #166534; }
        .footer { text-align: center; margin-top: 50px; color: #94a3b8; font-size: 12px; }
    </style>
    """

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--out", default="dashboard_executivo.html")
    args = parser.parse_args()

    # Coleta de dados avançada: Hash, Autor, Data, Mensagem (Assunto)
    raw_log = run_git(["log", "--pretty=format:%H|%an|%ad|%s", "--date=short", "--numstat"], args.repo)
    
    commits = []
    lines = raw_log.splitlines()
    curr = None
    
    for line in lines:
        if "|" in line:
            parts = line.split("|")
            curr = {"author": parts[1], "date": parts[2], "msg": parts[3], "add": 0, "del": 0}
            commits.append(curr)
        elif curr and "\t" in line:
            s = line.split("\t")
            if s[0].isdigit(): curr["add"] += int(s[0])
            if s[1].isdigit(): curr["del"] += int(s[1])

    # Agregações por Autor
    stats = {}
    for c in commits:
        a = c["author"]
        if a not in stats: stats[a] = {"c": 0, "add": 0, "del": 0, "last": ""}
        stats[a]["c"] += 1
        stats[a]["add"] += c["add"]
        stats[a]["del"] += c["del"]
        stats[a]["last"] = c["date"]

    sorted_authors = sorted(stats.items(), key=lambda x: x[1]["c"], reverse=True)

    # HTML
    h = []
    push(h, "<!DOCTYPE html><html><head><meta charset='utf-8'>")
    push(h, "<title>Relatório Executivo de Engenharia</title>")
    push(h, get_css() + "</head><body><div class='container'>")

    # Header
    push(h, "<div class='header'><div><h1>Dashboard de Atividade de Engenharia</h1>")
    push(h, "<p style='color:#64748b; margin:5px 0 0 0;'>Análise de performance e evolução de código-fonte</p></div>")
    push(h, f"<div style='text-align:right'><span class='badge'>CONFIDENCIAL</span><br>")
    push(h, f"<small>{datetime.now().strftime('%d/%m/%Y %H:%M')}</small></div></div>")

    # KPIs
    push(h, "<div class='grid'>")
    push(h, f"<div class='kpi-card'><span class='kpi-lab'>Volume de Commits</span><span class='kpi-val'>{fmt(len(commits))}</span></div>")
    push(h, f"<div class='kpi-card'><span class='kpi-lab'>Contribuidores Ativos</span><span class='kpi-val'>{len(stats)}</span></div>")
    push(h, f"<div class='kpi-card'><span class='kpi-lab'>Linhas Adicionadas</span><span class='kpi-val'>{fmt(sum(s['add'] for s in stats.values()))}</span></div>")
    push(h, f"<div class='kpi-card'><span class='kpi-lab'>Total de Refatoração (Remoções)</span><span class='kpi-val'>{fmt(sum(s['del'] for s in stats.values()))}</span></div>")
    push(h, "</div>")

    # Performance dos Profissionais
    push(h, "<div class='card'><div class='card-title'>Desempenho por Profissional</div>")
    push(h, "<table><thead><tr><th>Profissional</th><th>Entregas (Commits)</th><th>Linhas (+)</th><th>Linhas (-)</th><th>Última Atividade</th></tr></thead><tbody>")
    for auth, s in sorted_authors:
        push(h, f"<tr><td><b>{esc(auth)}</b></td><td>{fmt(s['c'])}</td><td>{fmt(s['add'])}</td><td>{fmt(s['del'])}</td><td>{s['last']}</td></tr>")
    push(h, "</tbody></table></div>")

    # Qualidade de Documentação (Commits)
    push(h, "<div class='card'><div class='card-title'>Log de Evolução e Comentários (Amostra Recente)</div>")
    push(h, "<table><thead><tr><th>Data</th><th>Autor</th><th>Mensagem de Alteração</th></tr></thead><tbody>")
    for c in commits[:15]:  # Mostra os 15 mais recentes
        push(h, f"<tr><td style='white-space:nowrap'>{c['date']}</td><td>{esc(c['author'])}</td><td>{esc(c['msg'])}</td></tr>")
    push(h, "</tbody></table>")
    push(h, "<p style='font-size:12px; color:#94a3b8; margin-top:10px;'>* Mensagens claras indicam boa cultura de documentação e rastreabilidade técnica.</p></div>")

    push(h, "<div class='footer'>Relatório Gerado Automaticamente - Métricas de Git</div>")
    push(h, "</div></body></html>")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("".join(h))
    print(f"Relatório pronto: {os.path.abspath(args.out)}")

if __name__ == "__main__":
    main()
