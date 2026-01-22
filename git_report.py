import os
import datetime

# Configurações de Estilo Executivo
CSS_DASHBOARD = """
<style>
    :root { --cobalt: #1e3a8a; --slate: #334155; --emerald: #10b981; --bg: #f8fafc; }
    body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--slate); margin: 0; padding: 40px; }
    .container { max-width: 1200px; margin: 0 auto; }
    .header { text-align: center; margin-bottom: 50px; }
    h1 { color: var(--cobalt); font-size: 32px; font-weight: 800; margin-bottom: 10px; }
    .subtitle { color: #64748b; font-size: 16px; }
    
    /* Grid de KPIs */
    .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }
    .kpi-card { background: white; padding: 25px; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; }
    .kpi-title { font-size: 12px; text-transform: uppercase; font-weight: 700; color: #94a3b8; letter-spacing: 1px; }
    .kpi-value { font-size: 30px; font-weight: 800; color: var(--cobalt); display: block; margin-top: 5px; }

    /* Lista de Projetos */
    .project-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; }
    .project-card { 
        background: white; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0;
        transition: transform 0.2s; text-decoration: none; color: inherit; display: flex; justify-content: space-between; align-items: center;
    }
    .project-card:hover { transform: translateY(-3px); border-color: var(--cobalt); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
    .project-info b { color: var(--cobalt); font-size: 16px; }
    .project-links { display: flex; gap: 10px; }
    .btn { padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; text-decoration: none; }
    .btn-main { background: #eff6ff; color: #2563eb; }
    .btn-sub { background: #f0fdf4; color: #166534; }
    
    .footer { margin-top: 60px; text-align: center; font-size: 12px; color: #94a3b8; }
</style>
"""

def generate_executive_index(repos_data, output_path="index.html"):
    """
    repos_data: lista de dicionários com { 'name': str, 'commits': int, 'url_geral': str, 'url_90d': str }
    """
    html = [
        "<!DOCTYPE html><html lang='pt-br'><head><meta charset='utf-8'>",
        "<title>Executive Engineering Dashboard</title>",
        CSS_DASHBOARD,
        "</head><body><div class='container'>"
    ]

    # Header
    html.append("<div class='header'>")
    html.append("<h1>Painel Executivo de Engenharia</h1>")
    html.append("<p class='subtitle'>Métricas Consolidadas de Performance e Entrega Técnica</p>")
    html.append("</div>")

    # KPIs Globais (Simulados com base nos seus 18 repositórios)
    total_repos = len(repos_data)
    html.append(f"""
    <div class='kpi-grid'>
        <div class='kpi-card'><span class='kpi-title'>Total de Projetos</span><span class='kpi-value'>{total_repos}</span></div>
        <div class='kpi-card'><span class='kpi-title'>Status da Pipeline</span><span class='kpi-value' style='color:var(--emerald)'>Ativa</span></div>
        <div class='kpi-card'><span class='kpi-title'>Última Atualização</span><span class='kpi-value' style='font-size:18px'>{datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}</span></div>
    </div>
    """)

    # Grid de Projetos
    html.append("<h2 style='font-size:20px; margin-bottom:20px;'>Portfólio de Repositórios</h2>")
    html.append("<div class='project-grid'>")
    
    for repo in repos_data:
        html.append(f"""
        <div class='project-card'>
            <div class='project-info'>
                <b>{repo['name']}</b><br>
                <small style='color:#94a3b8'>Repositório Ativo</small>
            </div>
            <div class='project-links'>
                <a href='{repo['url_geral']}' class='btn btn-main'>Visão Geral</a>
                <a href='{repo['url_90d']}' class='btn btn-sub'>Últimos 90 Dias</a>
            </div>
        </div>
        """)
    
    html.append("</div>") # Fim project-grid
    html.append("<div class='footer'>Relatório gerado via GitHub Actions | Governança de TI</div>")
    html.append("</div></body></html>")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html))

# Exemplo de uso para integrar no seu loop de repositórios
if __name__ == "__main__":
    # Esta lista deve ser preenchida dinamicamente pelo seu script principal
    exemplo_repos = [
        {'name': 'BoasNoticias', 'url_geral': 'site/-BoasNoticias.html', 'url_90d': 'site/-BoasNoticias_90d.html'},
        {'name': 'android-marvel-app', 'url_geral': 'site/android-marvel-app.html', 'url_90d': 'site/android-marvel-app_90d.html'},
        # ... adicionar os outros 16 repositórios aqui
    ]
    generate_executive_index(exemplo_repos)
