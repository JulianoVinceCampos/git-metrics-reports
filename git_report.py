import subprocess
import os
import argparse
from collections import Counter
from datetime import datetime

# Configurações globais
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
        :root { --primary: #0f172a; --accent: #3b82f6; --bg: #f1f5f9; --white: #ffffff; --border: #e2e8f0; --text-main: #334155; }
        body { font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: var(--bg); color: var(--text-main); margin: 0; padding: 40px; }
        .container { max-width: 1100px; margin: 0 auto; }
        .header { border-bottom: 3px solid var(--primary); padding-bottom: 20px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: flex-end; }
        h1 { margin: 0; color: var(--primary); font-size: 26px; text-transform: uppercase; letter-spacing: 0.5px; }
        .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 35px; }
        .kpi-card { background: var(--white); padding: 18px; border-radius: 10px; border: 1px solid var(--border); box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .kpi-val { font-size: 28px; font-weight: 800; color: var(--accent); display: block; margin-bottom: 4px; }
        .kpi-lab { font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; }
        .card { background: var(--white); padding: 25px; border-radius: 12px; border: 1px solid var(--border); margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        .card-title { font-size: 16px; font-weight: 700; margin-bottom: 20px; color: var(--primary); border-left: 5px solid var(--accent); padding-left: 12px; text-transform: uppercase; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th { text-align: left; padding: 12px; border-bottom: 2px solid var(--border); color: #475569; font-size: 12px; text-transform: uppercase; }
        td { padding: 12px; border-bottom: 1px solid var(--border); font-size: 13.5px; color: var(--text-main); }
        tr:hover { background: #f8fafc; }
        .chart-bar-bg { background: #f1f5f9; height: 8px; border-radius: 4px; width: 100px; display: inline-block; margin-right: 8px; }
        .chart-bar-fill { background: var(--accent); height: 8px; border-radius: 4px; }
        .footer { text-align: center; margin-top: 40px; color: #94a3b8; font-size: 11px; border-top: 1px solid var(--border); padding-top: 20px; }
    </style>
    """

def main():
    parser = argparse.ArgumentParser(description="Gera um relatório executivo de atividades Git.")
    parser.add_argument("--repo", default=".", help="Caminho para o repositório")
    parser.add_argument("--out", default="site/index.html", help="Caminho de saída do arquivo HTML")
    parser.add_argument("--since", help="Filtrar commits desde uma data/período (ex: '90 days ago')")
    args = parser.parse_args()

    # Preparar argumentos do Git
    git_cmd = ["log", "--pretty=format:%H|%an|%ad|%s", "--date=short", "--numstat"]
    if args.since:
        git_cmd.append(f"--since={args.since}")

    raw_log = run_git(git_cmd, args.repo)
    if not raw_log:
        print("Nenhum dado encontrado para o período/repositório informado.")
        return

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

    # Consolidação de Métricas
    stats = {}
    for c in commits:
        a = c["author"]
        if a not in stats: stats[a] = {"c": 0, "add": 0, "del": 0, "last": ""}
        stats[a]["c"] += 1
        stats[a]["add"] += c["add"]
        stats[a]["del"] += c["del"]
        stats[a]["last"] = c["date"]

    sorted_authors = sorted(stats.items(), key=lambda x: x[1]["c"], reverse=True)
    max_commits = sorted_authors[0][1]["c"] if sorted_authors else 1

    # Construção do HTML
    h = []
    push(h, "<!DOCTYPE html><html lang='pt-br'><head><meta charset='utf-8'>")
    push(h, "<title>Dashboard de Engenharia | Relatório Executivo</title>")
    push(h, get_css() + "</head><body><div class='container'>")

    # Header Executivo
    push(h, "<div class='header'><div><h1>Sumário Executivo de Atividade Técnica</h1>")
    periodo = args.since if args.since else "Todo o histórico"
    push(h, f"<p style='color:#64748b; margin:5px 0 0 0;'>Análise de entrega de software | Período: <b>{esc(periodo)}</b></p></div>")
    push(h, f"<div style='text-align:right'><small style='color:#94a3b8'>Emitido em: {datetime.now().strftime('%d/%m/%Y %H:%M')}</small></div></div>")

    # KPIs de Alto Nível
    push(h, "<div class='grid'>")
    push(h, f"<div class='kpi-card'><span class='kpi-lab'>Entregas Realizadas</span><span class='kpi-val'>{fmt(len(commits))}</span></div>")
    push(h, f"<div class='kpi-card'><span class='kpi-lab'>Engenheiros Ativos</span><span class='kpi-val'>{len(stats)}</span></div>")
    push(h, f"<div class='kpi-card'><span class='kpi-lab'>Linhas de Valor (+)</span><span class='kpi-val'>{fmt(sum(s['add'] for s in stats.values()))}</span></div>")
    push(h, f"<div class='kpi-card'><span class='kpi-lab'>Otimização/Limpeza (-)</span><span class='kpi-val'>{fmt(sum(s['del'] for s in stats.values()))}</span></div>")
    push(h, "</div>")

    # Tabela de Performance dos Profissionais
    push(h, "<div class='card'><div class='card-title'>Desempenho por Profissional</div>")
    push(h, "<table><thead><tr><th>Profissional</th><th>Participação</th><th>Volume (Commits)</th><th>Novas Linhas</th><th>Limpeza</th><th>Última Entrega</th></tr></thead><tbody>")
    for auth, s in sorted_authors:
        pct = (s['c'] / max_commits) * 100
        push(h, f"<tr><td><b>{esc(auth)}</b></td>")
        push(h, f"<td><div class='chart-bar-bg'><div class='chart-bar-fill' style='width:{pct}%'></div></div></td>")
        push(h, f"<td>{fmt(s['c'])}</td><td>{fmt(s['add'])}</td><td>{fmt(s['del'])}</td><td>{s['last']}</td></tr>")
    push(h, "</tbody></table></div>")

    # Log de Comentários e Intencionalidade
    push(h, "<div class='card'><div class='card-title'>Rastreabilidade: Comentários e Intencionalidade</div>")
    push(h, "<p style='font-size:13px; color:#64748b; margin-bottom:15px;'>As 15 alterações mais recentes e seus objetivos declarados:</p>")
    push(h, "<table><thead><tr><th>Data</th><th>Autor</th><th>Objetivo da Alteração</th></tr></thead><tbody>")
    for c in commits[:15]:
        push(h, f"<tr><td style='white-space:nowrap'>{c['date']}</td><td>{esc(c['author'])}</td><td>{esc(c['msg'])}</td></tr>")
    push(h, "</tbody></table></div>")

    push(h, "<div class='footer'>Este relatório é gerado automaticamente para fins de governança e auditoria técnica.</div>")
    push(h, "</div></body></html>")

    # Garantir que o diretório de saída existe
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("".join(h))
    print(f"Relatório executivo gerado com sucesso em: {args.out}")

if __name__ == "__main__":
    main()
