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
  }
  .project-card:hover { transform:translateY(-5px); box-shadow:0 10px 15px -3px rgba(0,0,0,0.1); border-color:var(--accent); }
  .project-name { font-size:18px; font-weight:700; margin-bottom:10px; color:var(--primary); }

  .btn-group { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:18px; }
  .btn { padding:10px; border-radius:8px; font-size:13px; font-weight:600; text-align:center; text-decoration:none; transition:background .2s, opacity .2s; }
  .btn-primary { background:#eff6ff; color:#2563eb; border:1px solid #bfdbfe; }
  .btn-primary:hover { background:#dbeafe; }
  .btn-secondary { background:#f0fdf4; color:#166534; border:1px solid #bbf7d0; }
  .btn-secondary:hover { background:#dcfce7; }

  .btn-disabled { opacity:.45; pointer-events:none; cursor:not-allowed; }
  .footer { text-align:center; margin-top:60px; color:#94a3b8; font-size:13px; }

  /* --- Card clicável (vira link) --- */
  .card-link { color: inherit; text-decoration: none; }
  .card-link:hover { color: inherit; text-decoration: none; }

  /* --- Selo executivo --- */
  .exec-badge {
    margin-top: 6px;
    padding: 10px 12px;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    background: #f8fafc;
  }
  .exec-badge-title {
    display:block;
    font-size: 12px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: .4px;
    color: #0f172a;
    margin-bottom: 4px;
  }
  .exec-badge-desc {
    display:block;
    font-size: 12px;
    color: #475569;
    line-height: 1.35;
  }
</style>
"""

def sanitize_repo_name(name: str) -> str:
    return name.strip().lstrip("-").strip()

def detect_reports_dir() -> str:
    if os.path.isdir("site"):
        htmls = [f for f in os.listdir("site") if f.endswith(".html")]
        if htmls:
            return "site"
    return "."

def file_exists(rel_path: str) -> bool:
    return os.path.isfile(rel_path)

def make_href(reports_dir: str, filename: str) -> str:
    if reports_dir == ".":
        return filename
    return f"{reports_dir}/{filename}"

def generate_portal(repos_list, output_file="index.html"):
    now = datetime.datetime.now()
    reports_dir = detect_reports_dir()

    repos = [sanitize_repo_name(r) for r in repos_list]
    repos = [r for r in repos if r]

    html = [
        "<!DOCTYPE html><html lang='pt-br'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<title>Engenharia | Dashboard Executivo</title>",
        CSS_DASHBOARD,
        "</head><body><div class='container'>"
    ]

    html.append(f"""
    <div class='header'>
      <div>
        <h1>Dashboard Executivo de Engenharia</h1>
        <p style='color:#64748b; margin:5px 0 0 0;'>
          Consolidado de performance • Fonte: Git Metrics • Diretório: <b>{reports_dir}</b>
        </p>
      </div>
      <span class='status-tag'>● ATUALIZADO</span>
    </div>
    """)

    html.append(f"""
    <div class='kpi-grid'>
      <div class='kpi-card'><span class='kpi-label'>Total de Projetos</span><span class='kpi-value'>{len(repos)}</span></div>
      <div class='kpi-card'><span class='kpi-label'>Última Extração</span><span class='kpi-value' style='font-size:20px;'>{now.strftime('%d/%m/%Y')}</span></div>
      <div class='kpi-card'><span class='kpi-label'>Hora da Geração</span><span class='kpi-value' style='font-size:20px;'>{now.strftime('%H:%M:%S')}</span></div>
    </div>
    """)

    html.append("<div class='project-grid'>")

    for repo in repos:
        geral_file = f"{repo}.html"
        trend_file = f"{repo}_90d.html"  # mantém o mesmo arquivo, só muda o texto no botão

        geral_path = os.path.join(reports_dir, geral_file) if reports_dir != "." else geral_file
        trend_path = os.path.join(reports_dir, trend_file) if reports_dir != "." else trend_file

        geral_ok = file_exists(geral_path)
        trend_ok = file_exists(trend_path)

        geral_href = make_href(reports_dir, geral_file) if geral_ok else "#"
        trend_href = make_href(reports_dir, trend_file) if trend_ok else "#"

        geral_cls = "btn btn-primary" + ("" if geral_ok else " btn-disabled")
        trend_cls = "btn btn-secondary" + ("" if trend_ok else " btn-disabled")

        # Card inteiro clicável se existir o relatório geral
        card_open = f"<a class='project-card card-link' href='{geral_href}'>" if geral_ok else "<div class='project-card'>"
        card_close = "</a>" if geral_ok else "</div>"

        highlight_title = "Pulso do Projeto"
        highlight_desc = "Visão executiva de ritmo de entrega, estabilidade e volume de mudanças."

        html.append(f"""
        {card_open}
          <div>
            <div class='project-name'>{repo}</div>

            <div class='exec-badge'>
              <span class='exec-badge-title'>{highlight_title}</span>
              <span class='exec-badge-desc'>{highlight_desc}</span>
            </div>

            <div style='font-size:12px; color:#64748b; margin-top:10px;'>
              Indicadores derivados de histórico de commits e alterações.
            </div>

            <div class='btn-group'>
              <a href='{geral_href}' class='{geral_cls}' onclick="event.stopPropagation();">Relatório Executivo</a>
              <a href='{trend_href}' class='{trend_cls}' onclick="event.stopPropagation();">Tendência de Atividade</a>
            </div>
          </div>
        {card_close}
        """)

    html.append("</div>")
    html.append(f"<div class='footer'>Atualizado automaticamente via GitHub Actions em {now.strftime('%d/%m/%Y %H:%M:%S')}</div>")
    html.append("</div></body></html>")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html))

meus_repos = [
    "-BoasNoticias", "android-marvel-app", "AndroidCoroutinesRetrofitMVVM",
    "CoronaStatus", "DiariodeNoticias", "dogs", "First_app_flutter",
    "git-metrics-reports", "julianoVinceCampos", "KotlinProjectJVDC",
    "MemoryNotes", "MovieApp", "notas", "Projeto-Android-Santander",
    "Projeto-Animals", "Projeto-IOS-telas-responsivas", "ReactHooksUniverseApp"
]

generate_portal(meus_repos)
