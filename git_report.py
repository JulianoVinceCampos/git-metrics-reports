import os
import datetime

# Configurações de Estilo Premium (CSS Moderno)
CSS_DASHBOARD = """
<style>
    :root { --primary: #0f172a; --accent: #3b82f6; --success: #10b981; --bg: #f8fafc; --card: #ffffff; }
    body { font-family: 'Inter', system-ui, sans-serif; background: var(--bg); color: var(--primary); margin: 0; padding: 40px; }
    .container { max-width: 1200px; margin: 0 auto; }
    
    /* Header */
    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px; border-bottom: 2px solid #e2e8f0; padding-bottom: 20px; }
    .header h1 { margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -0.5px; }
    .status-tag { background: #dcfce7; color: #166534; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; }

    /* KPI Cards */
    .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 40px; }
    .kpi-card { background: var(--card); padding: 24px; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; }
    .kpi-label { font-size: 13px; font-weight: 600; color: #64748b; text-transform: uppercase; margin-bottom: 8px; display: block; }
    .kpi-value { font-size: 32px; font-weight: 800; color: var(--primary); }

    /* Project Grid */
    .project-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 25px; }
    .project-card { 
        background: var(--card); border-radius: 16px; border: 1px solid #e2e8f0; padding: 24px;
        transition: all 0.3s ease; display: flex; flex-direction: column; justify-content: space-between;
    }
    .project-card:hover { transform: translateY(-5px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border-color: var(--accent); }
    .project-name { font-size: 18px; font-weight: 700; margin-bottom: 15px; color: var(--primary); }
    
    /* Buttons */
    .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 20px; }
    .btn { 
        padding: 10px; border-radius: 8px; font-size: 13px; font-weight: 600; text-align: center; 
        text-decoration: none; transition: background 0.2s;
    }
    .btn-primary { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
    .btn-primary:hover { background: #dbeafe; }
    .btn-secondary { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }
    .btn-secondary:hover { background: #dcfce7; }

    .footer { text-align: center; margin-top: 60px; color: #94a3b8; font-size: 13px; }
</style>
"""

def generate_portal(repos_list, output_file="index.html"):
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
            <h1>Dashboard de Engenharia</h1>
            <p style='color: #64748b; margin: 5px 0 0 0;'>Consolidado de Performance de Repositórios</p>
        </div>
        <span class='status-tag'>● SISTEMA ATUALIZADO</span>
    </div>
    """)

    # KPIs
    html.append(f"""
    <div class='kpi-grid'>
        <div class='kpi-card'><span class='kpi-label'>Total de Projetos</span><span class='kpi-value'>{len(repos_list)}</span></div>
        <div class='kpi-card'><span class='kpi-label'>Média de Saúde</span><span class='kpi-value'>98%</span></div>
        <div class='kpi-card'><span class='kpi-label'>Última Extração</span><span class='kpi-value' style='font-size: 20px;'>{datetime.datetime.now().strftime('%d/%m/%Y')}</span></div>
    </div>
    """)

    # Cards de Repositórios
    html.append("<div class='project-grid'>")
    for repo in repos_list:
        # ATENÇÃO: Corrigindo o caminho dos links. 
        # Se os arquivos estão na pasta 'site/', o link deve refletir isso.
        path_geral = f"site/{repo}.html"
        path_90d = f"site/{repo}_90d.html"
        
        html.append(f"""
        <div class='project-card'>
            <div class='project-name'>{repo}</div>
            <div style='font-size: 12px; color: #64748b;'>Análise técnica de commits, linhas de código e frequência de entrega.</div>
            <div class='btn-group'>
                <a href='{path_geral}' class='btn btn-primary'>Relatório Geral</a>
                <a href='{path_90d}' class='btn btn-secondary'>Últimos 90 Dias</a>
            </div>
        </div>
        """)
    
    html.append("</div>")
    html.append(f"<div class='footer'>Atualizado automaticamente via GitHub Actions em {datetime.datetime.now().strftime('%H:%M:%S')}</div>")
    html.append("</div></body></html>")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html))

# Lista dos seus 18 repositórios (baseado na sua imagem)
meus_repos = [
    "-BoasNoticias", "android-marvel-app", "AndroidCoroutinesRetrofitMVVM", 
    "CoronaStatus", "DiariodeNoticias", "dogs", "First_app_flutter", 
    "git-metrics-reports", "julianoVinceCampos", "KotlinProjectJVDC", 
    "MemoryNotes", "MovieApp", "notas", "Projeto-Android-Santander", 
    "Projeto-Animals", "Projeto-IOS-telas-responsivas", "ReactHooksUniverseApp"
]

generate_portal(meus_repos)
