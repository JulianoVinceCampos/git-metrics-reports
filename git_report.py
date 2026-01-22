import os
import datetime

CSS_DASHBOARD = """
<style>
  :root { --primary:#0f172a; --accent:#3b82f6; --success:#10b981; --bg:#f8fafc; --card:#ffffff; }
  body { font-family: Inter, system-ui, sans-serif; background: var(--bg); color: var(--primary); margin:0; padding:40px; }
  .container { max-width:1200px; margin:0 auto; }

  .header { display:flex; justify-content:space-between; align-items:center; margin-bottom:40px; border-bottom:2px solid #e2e8f0; padding-bottom:20px; }
  .header h1 { margin:0; font-size:28px; font-weight:800; letter-spacing:-0.5px; }
  .status-tag { background:#dcfce7; color:#166534; padding:6px 12px; border-radius:20px; font-size:12px; font-weight:700; }

  .kpi-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:20px; margin-bottom:40px; }
  .kpi-card { background:var(--card); padding:24px; border-radius:16px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.1); border:1px solid #e2e8f0; }
  .kpi-label { font-size:13px; font-weight:600; color:#64748b; text-transform:uppercase; margin-bottom:8px; display:block; }
  .kpi-value { font-size:32px; font-weight:800; color:var(--primary); }

  .project-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(320px, 1fr)); gap:25px; }

  .project-card {
    background:var(--card); border-radius:16px; border:1px solid #e2e8f0; padding:24px;
    transition:all .3s ease; display:flex; flex-direction:column; justify-content:space-between;
    cursor: pointer; position: relative;
  }
  .project-card:hover { transform:translateY(-5px); box-shadow:0 10px 15px -3px rgba(0,0,0,0.1); border-color:var(--accent); }
  .project-name { font-size:18px; font-weight:700; margin-bottom:15px; color:var(--primary); }

  .btn-group { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:18px; z-index: 10; }
  .btn { padding:10px; border-radius:8px; font-size:13px; font-weight:600; text-align:center; text-decoration:none; transition:background .2s; }
  .btn-primary { background:#eff6ff; color:#2563eb; border:1px solid #bfdbfe; }
  .btn-primary:hover { background:#dbeafe; }
  .btn-secondary { background:#f0fdf4; color:#166534; border:1px solid #bbf7d0; }
  .btn-secondary:hover { background:#dcfce7; }

  .footer { text-align:center; margin-top:60px; color:#94a3b8; font-size:13px; }

  .info-text { font-size:12px; color:#64748b; margin-top:12px; line-height:1.4; }
</style>
"""

def sanitize_repo_name(name: str) -> str:
    # Remove hífens iniciais e espaços
    return name.strip().lstrip("-").strip()

def generate_portal(repos_list, output_file="index.html"):
    now = datetime.datetime.now()
    
    # Lista limpa de repositórios
    repos = [sanitize_repo_name(r) for r in repos_list if r]

    html = [
        "<!DOCTYPE html><html lang='pt-br'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<title>Engenharia | Dashboard Executivo</title>",
        CSS_DASHBOARD,
        "</head><body><div class='container'>"
    ]

    # Header
    html.append(f"""
    <div class='header'>
      <div>
        <h1>Dashboard Executivo de Engenharia</h1>
        <p style='color:#64748b; margin:5px 0 0 0;'>Consolidado de performance • Fonte: Git Metrics</p>
      </div>
      <span class='status-tag'>● ATUALIZADO</span>
    </div>
    """)

    # KPIs
    html.append(f"""
    <div class='kpi-grid'>
      <div class='kpi-card'><span class='kpi-label'>Total de Projetos</span><span class='kpi-value'>{len(repos)}</span></div>
      <div class='kpi-card'><span class='kpi-label'>Última Extração</span><span class='kpi-value' style='font-size:20px;'>{now.strftime('%d/%m/%Y')}</span></div>
      <div class='kpi-card'><span class='kpi-label'>Hora da Geração</span><span class='kpi-value' style='font-size:20px;'>{now.strftime('%H:%M:%S')}</span></div>
    </div>
    """)

    html.append("<div class='project-grid'>")

    for repo in repos:
        # Caminhos relativos para os arquivos HTML gerados pelo Git Metrics
        # Assume-se que os arquivos estão na mesma pasta do index.html ou no gh-pages
        executivo_href = f"{repo}.html"
        tendencia_href = f"{repo}_90d.html"

        html.append(f"""
        <div class='project-card' onclick="window.location.href='{executivo_href}'">
          <div>
            <div class='project-name'>{repo}</div>
            
            <div style='background:#f1f5f9; padding:10px; border-radius:8px; border: 1px dashed #cbd5e1;'>
                <span style='font-size:11px; font-weight:bold; color:#475569; text-transform:uppercase;'>Status de Relatório</span>
                <p class='info-text' style='margin-top:5px;'>Dados consolidados de commits, pull requests e frequência de deploy.</p>
            </div>

            <div class='btn-group'>
              <a href='{executivo_href}' class='btn btn-primary' onclick="event.stopPropagation();">Relatório Executivo</a>
              <a href='{tendencia_href}' class='btn btn-secondary' onclick="event.stopPropagation();">Tendência de Atividade</a>
            </div>
          </div>
        </div>
        """)

    html.append("</div>")
    html.append(f"<div class='footer'>Atualizado via GitHub Actions em {now.strftime('%d/%m/%Y %H:%M:%S')}</div>")
    html.append("</div></body></html>")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html))

# Execução
meus_repos = [
    "-BoasNoticias", "android-marvel-app", "AndroidCoroutinesRetrofitMVVM",
    "CoronaStatus", "DiariodeNoticias", "dogs", "First_app_flutter",
    "git-metrics-reports", "julianoVinceCampos", "KotlinProjectJVDC",
    "MemoryNotes", "MovieApp", "notas", "Projeto-Android-Santander",
    "Projeto-Animals", "Projeto-IOS-telas-responsivas", "ReactHooksUniverseApp"
]

generate_portal(meus_repos)
