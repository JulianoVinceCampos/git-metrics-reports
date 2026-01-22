import os
import datetime
from typing import Optional

CSS_DASHBOARD = """
<style>
  :root { --primary:#0f172a; --accent:#3b82f6; --success:#10b981; --danger:#ef4444; --bg:#f8fafc; --card:#ffffff; }
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
    position: relative;
  }
  .project-card.clickable { cursor:pointer; }
  .project-card:hover { transform:translateY(-5px); box-shadow:0 10px 15px -3px rgba(0,0,0,0.1); border-color:var(--accent); }

  .project-name { font-size:18px; font-weight:700; margin-bottom:12px; color:var(--primary); }

  .status-box {
    background:#f8fafc; padding:12px; border-radius:10px;
    border:1px dashed #cbd5e1; margin-bottom:12px;
  }
  .status-title { font-size:11px; font-weight:800; letter-spacing:.3px; color:#475569; text-transform:uppercase; display:flex; align-items:center; gap:8px; }
  .dot { width:8px; height:8px; border-radius:99px; display:inline-block; background:var(--success); }
  .dot.danger { background:var(--danger); }
  .info-text { font-size:12px; color:#64748b; margin:8px 0 0 0; line-height:1.4; }

  .btn-group { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:12px; z-index:10; }
  .btn { padding:10px; border-radius:8px; font-size:13px; font-weight:700; text-align:center; text-decoration:none; transition:background .2s, opacity .2s; }
  .btn-primary { background:#eff6ff; color:#2563eb; border:1px solid #bfdbfe; }
  .btn-primary:hover { background:#dbeafe; }
  .btn-secondary { background:#f0fdf4; color:#166534; border:1px solid #bbf7d0; }
  .btn-secondary:hover { background:#dcfce7; }
  .btn-disabled { opacity:.45; pointer-events:none; cursor:not-allowed; }

  .footer { text-align:center; margin-top:60px; color:#94a3b8; font-size:13px; }
</style>
"""

def sanitize_display_name(name: str) -> str:
    # Só para exibição (não mexe no filename real)
    return name.strip().lstrip("-").strip()

def detect_reports_dir() -> str:
    """
    Detecta onde estão os HTMLs que serão publicados:
    - se existir ./site com HTMLs, usa 'site'
    - senão usa '.'
    """
    if os.path.isdir("site") and any(f.endswith(".html") for f in os.listdir("site")):
        return "site"
    return "."

def list_html_files(reports_dir: str) -> set[str]:
    base = reports_dir if reports_dir != "." else "."
    try:
        return {f for f in os.listdir(base) if f.endswith(".html")}
    except FileNotFoundError:
        return set()

def choose_existing(files: set[str], candidates: list[str]) -> Optional[str]:
    for c in candidates:
        if c in files:
            return c
    return None

def make_href(reports_dir: str, filename: str) -> str:
    return filename if reports_dir == "." else f"{reports_dir}/{filename}"

def generate_portal(repos_list, output_file="index.html"):
    now = datetime.datetime.now()
    reports_dir = detect_reports_dir()
    files = list_html_files(reports_dir)

    repos_raw = [r for r in repos_list if r and r.strip()]
    total = len(repos_raw)

    html = [
        "<!DOCTYPE html><html lang='pt-br'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<title>Engenharia | Dashboard Executivo</title>",
        CSS_DASHBOARD,
        "</head><body><div class='container'>"
    ]

    # Header
    html.append("""
    <div class='header'>
      <div>
        <h1>Dashboard Executivo de Engenharia</h1>
        <p style='color:#64748b; margin:5px 0 0 0;'>
          Consolidado de performance • Fonte: Git Metrics
        </p>
      </div>
      <span class='status-tag'>● ATUALIZADO</span>
    </div>
    """)

    # KPIs
    html.append("""
    <div class='kpi-grid'>
      <div class='kpi-card'>
        <span class='kpi-label'>Total de Projetos</span>
        <span class='kpi-value'>{total}</span>
      </div>
      <div class='kpi-card'>
        <span class='kpi-label'>Última Extração</span>
        <span class='kpi-value' style='font-size:20px;'>{date}</span>
      </div>
      <div class='kpi-card'>
        <span class='kpi-label'>Hora da Geração</span>
        <span class='kpi-value' style='font-size:20px;'>{time}</span>
      </div>
    </div>
    """.format(
        total=total,
        date=now.strftime('%d/%m/%Y'),
        time=now.strftime('%H:%M:%S')
    ))

    html.append("<div class='project-grid'>")

    for repo_raw in repos_raw:
        display = sanitize_display_name(repo_raw)

        # Tentativas de nomes de arquivo (porque pode existir com e sem '-' no começo)
        exec_candidates = [
            f"{repo_raw}.html",
            f"{display}.html",
            f"{repo_raw}_(geral).html",
            f"{display}_(geral).html",
            f"{repo_raw}_geral.html",
            f"{display}_geral.html",
        ]
        trend_candidates = [
            f"{repo_raw}_90d.html",
            f"{display}_90d.html",
            f"{repo_raw}_90dias.html",
            f"{display}_90dias.html",
        ]

        exec_file = choose_existing(files, exec_candidates)
        trend_file = choose_existing(files, trend_candidates)

        exec_ok = exec_file is not None
        trend_ok = trend_file is not None

        exec_href = make_href(reports_dir, exec_file) if exec_ok else "#"
        trend_href = make_href(reports_dir, trend_file) if trend_ok else "#"

        card_cls = "project-card clickable" if exec_ok else "project-card"
        card_onclick = f"onclick=\"window.location.href='{exec_href}'\"" if exec_ok else ""

        if exec_ok or trend_ok:
            dot_class = "dot"
            status_title = "EVIDÊNCIA PUBLICADA"
            status_msg = "Visão executiva de ritmo de entrega, estabilidade e volume de mudanças."
        else:
            dot_class = "dot danger"
            status_title = "SEM EVIDÊNCIA PUBLICADA"
            status_msg = "Relatórios não encontrados no Pages. Verifique geração e deploy no gh-pages."

        exec_btn_cls = "btn btn-primary" + ("" if exec_ok else " btn-disabled")
        trend_btn_cls = "btn btn-secondary" + ("" if trend_ok else " btn-disabled")

        # CARD (SEM f-string de triple quote)
        card_html = """
        <div class='{card_cls}' {card_onclick}>
          <div>
            <div class='project-name'>{display}</div>

            <div class='status-box'>
              <div class='status-title'><span class='{dot_class}'></span>{status_title}</div>
              <p class='info-text'>{status_msg}</p>
            </div>

            <div class='info-text' style='margin-top:6px;'>
              Indicadores derivados de histórico de commits e alterações.
            </div>

            <div class='btn-group'>
              <a href='{exec_href}' class='{exec_btn_cls}' onclick="event.stopPropagation();">Relatório Executivo</a>
              <a href='{trend_href}' class='{trend_btn_cls}' onclick="event.stopPropagation();">Tendência de Atividade</a>
            </div>
          </div>
        </div>
        """.format(
            card_cls=card_cls,
            card_onclick=card_onclick,
            display=display,
            dot_class=dot_class,
            status_title=status_title,
            status_msg=status_msg,
            exec_href=exec_href,
            trend_href=trend_href,
            exec_btn_cls=exec_btn_cls,
            trend_btn_cls=trend_btn_cls
        )

        html.append(card_html)

    html.append("</div>")
    html.append("<div class='footer'>Atualizado via GitHub Actions em {dt}</div>".format(
        dt=now.strftime('%d/%m/%Y %H:%M:%S')
    ))
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

generate_portal(meus_repos, output_file="index.html")
