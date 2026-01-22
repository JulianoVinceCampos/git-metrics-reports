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
    # só para exibição (não mexe no filename real)
    return name.strip().lstrip("-").strip()

def detect_reports_dir() -> str:
    """
    Detecta onde estão os HTMLs que serão publicados:
    - se existir ./site com HTMLs, usa 'site'
    - senão usa '.'
    """
    if os.path.isdir("site"):
        if any(f.endswith(".html") for f in os.listdir("site")):
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
    # href relativo ao index.html
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

    html.append(f"""
    <div class='header'>
      <div>
        <h1>Dashboard Executivo de Engenharia</h1>
        <p style='color:#64748b; margin:5px 0
