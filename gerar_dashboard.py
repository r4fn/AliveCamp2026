import pandas as pd
import json
import sys
from pathlib import Path

# ── Lê a planilha ─────────────────────────────────────────────────────────────
xlsx_path = Path("dados/123.xlsx")
if not xlsx_path.exists():
    print("ERRO: arquivo dados/inscricoes.xlsx não encontrado.")
    sys.exit(1)

df = pd.read_excel(xlsx_path)

# Filtra apenas inscrições reais (com timestamp)
real = df[df['Carimbo de data/hora'].notna()].copy()

# ── Métricas principais ────────────────────────────────────────────────────────
total_inscritos = len(real)

# Financeiro (inclui linhas de notas avulsas)
total_pago     = df['Valores Pagos'].fillna(0).sum()
total_falta    = df['Falta pagar'].fillna(0).sum()
total_previsto = total_pago + total_falta

quitados  = int((real['Falta pagar'].fillna(0) == 0).sum())
pendentes = int((real['Falta pagar'].fillna(0) > 0).sum())

# Igrejas
igrejas = (
    real['Você é membro de alguma igreja? Qual?']
    .value_counts()
    .head(8)
    .to_dict()
)
total_igrejas = int(real['Você é membro de alguma igreja? Qual?'].nunique())

# Faixas etárias
bins   = [0, 12, 17, 25, 35, 200]
labels = ['Criança (0–12)', 'Adolesc. (13–17)', 'Jovem (18–25)', 'Adulto (26–35)', 'Adulto+ (36+)']
real['faixa'] = pd.cut(real['Idade'], bins=bins, labels=labels)
faixas = real['faixa'].value_counts().reindex(labels).fillna(0).astype(int).to_dict()

# Pagamentos
pagamentos_raw = real['✅ COMO DESEJA PARTICIPAR?'].value_counts().to_dict()
pagamentos = {}
for k, v in pagamentos_raw.items():
    if 'VISTA' in str(k):       pagamentos['À Vista'] = pagamentos.get('À Vista', 0) + v
    elif 'PIX' in str(k) and 'DIÁRIA' not in str(k): pagamentos['Camp. Completo PIX'] = pagamentos.get('Camp. Completo PIX', 0) + v
    elif 'PARCELADO' in str(k): pagamentos['Parcelado 5x'] = pagamentos.get('Parcelado 5x', 0) + v
    elif 'CARTÃO' in str(k):    pagamentos['Cartão'] = pagamentos.get('Cartão', 0) + v
    elif 'DIÁRIA' in str(k):    pagamentos['Diária PIX'] = pagamentos.get('Diária PIX', 0) + v

# Timeline por mês
real['mes_str'] = real['Carimbo de data/hora'].dt.strftime('%b/%Y')
real['mes_ord'] = real['Carimbo de data/hora'].dt.to_period('M')
timeline = (
    real.groupby('mes_ord')
    .size()
    .reset_index(name='count')
    .sort_values('mes_ord')
)
timeline['label'] = timeline['mes_ord'].dt.strftime('%b/%y')
timeline_data = [
    {"label": row['label'], "count": int(row['count'])}
    for _, row in timeline.iterrows()
]

# ── Monta o JSON de dados ──────────────────────────────────────────────────────
dados = {
    "total_inscritos":  total_inscritos,
    "total_pago":       round(total_pago, 2),
    "total_falta":      round(total_falta, 2),
    "total_previsto":   round(total_previsto, 2),
    "total_igrejas":    total_igrejas,
    "quitados":         quitados,
    "pendentes":        pendentes,
    "igrejas":          igrejas,
    "faixas":           faixas,
    "pagamentos":       pagamentos,
    "timeline":         timeline_data,
}

# ── Percentuais ───────────────────────────────────────────────────────────────
pct_pago  = round(total_pago  / total_previsto * 100) if total_previsto > 0 else 0
pct_falta = round(total_falta / total_previsto * 100) if total_previsto > 0 else 0

# Igreja líder
igreja_lider = list(igrejas.keys())[0] if igrejas else "—"
pct_lider    = round(list(igrejas.values())[0] / total_inscritos * 100) if total_inscritos > 0 else 0

# Timeline: últimos 2 meses
ultimos = timeline_data[-2:] if len(timeline_data) >= 2 else timeline_data
pct_ultimos = round(sum(m['count'] for m in ultimos) / total_inscritos * 100) if total_inscritos > 0 else 0

# Igrejas para HTML
igrejas_html = ""
max_val = max(igrejas.values()) if igrejas else 1
cores_extra = ['#a78bfa', '#ff6b6b', '#4fc3f7', '#f6c90e']
for i, (nome, qtd) in enumerate(igrejas.items()):
    pct = round(qtd / max_val * 100)
    rank = f"#{i+1}" if i < 5 else "—"
    cor_barra = "linear-gradient(90deg, #f6c90e, #3ddc84)" if i < 5 else f"linear-gradient(90deg, {cores_extra[min(i-5,3)]}, {cores_extra[min(i-5,3)]}88)"
    cor_num   = "#f6c90e" if i < 5 else cores_extra[min(i-5, 3)]
    igrejas_html += f"""
        <li class="church-item">
          <span class="church-rank">{rank}</span>
          <span class="church-name">{nome}</span>
          <div class="church-bar-bg"><div class="church-bar-fill" style="width:{pct}%;background:{cor_barra}"></div></div>
          <span class="church-count" style="color:{cor_num}">{qtd}</span>
        </li>"""

# Timeline HTML
tl_max = max(m['count'] for m in timeline_data) if timeline_data else 1
cores_tl = ['rgba(139,148,158,0.7)', '#4fc3f7', '#a78bfa', '#4fc3f7', '#f6c90e', '#3ddc84']
timeline_html = ""
for i, m in enumerate(timeline_data):
    h_pct = max(5, round(m['count'] / tl_max * 100))
    cor   = cores_tl[i] if i < len(cores_tl) else '#f6c90e'
    star  = ' ⚡' if m['count'] == tl_max else ''
    label_br = m['label'].replace('/', '<br>')
    timeline_html += f"""
      <div class="tl-col">
        <span class="tl-num" style="color:{cor}">{m['count']}</span>
        <div class="tl-bar" style="height:{h_pct}%;background:linear-gradient(180deg,{cor},{cor}33)"></div>
        <span class="tl-label">{label_br}{star}</span>
      </div>"""

# Dados JS
faixas_labels = list(faixas.keys())
faixas_values = list(faixas.values())
pag_labels    = list(pagamentos.keys())
pag_values    = list(pagamentos.values())

# ── Gera o HTML ───────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>ALIVE CAMP 12ª Edição — Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Mono:wght@400;500&family=Outfit:wght@300;400;500;600&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  :root {{
    --bg:#0d1117;--surface:#161b22;--surface2:#1e2530;--border:#2d3748;
    --gold:#f6c90e;--green:#3ddc84;--coral:#ff6b6b;--sky:#4fc3f7;
    --purple:#a78bfa;--text:#e6edf3;--muted:#8b949e;
  }}
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{background:var(--bg);color:var(--text);font-family:'Outfit',sans-serif;min-height:100vh;overflow-x:hidden}}
  body::before{{content:'';position:fixed;inset:0;background-image:
    radial-gradient(ellipse at 20% 20%,rgba(246,201,14,.06) 0%,transparent 50%),
    radial-gradient(ellipse at 80% 80%,rgba(61,220,132,.05) 0%,transparent 50%);
    pointer-events:none;z-index:0}}
  .container{{max-width:1280px;margin:0 auto;padding:40px 24px;position:relative;z-index:1}}
  .header{{text-align:center;margin-bottom:48px}}
  .header-badge{{display:inline-block;font-family:'DM Mono',monospace;font-size:11px;letter-spacing:3px;
    text-transform:uppercase;color:var(--gold);border:1px solid rgba(246,201,14,.3);
    padding:6px 18px;border-radius:20px;margin-bottom:16px;background:rgba(246,201,14,.05)}}
  .header h1{{font-family:'Playfair Display',serif;font-size:clamp(36px,6vw,72px);font-weight:900;
    line-height:1;letter-spacing:-2px;background:linear-gradient(135deg,#f6c90e 0%,#fff 50%,#3ddc84 100%);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:10px}}
  .header-sub{{font-size:15px;color:var(--muted);letter-spacing:1px;font-weight:300}}
  .header-line{{width:80px;height:3px;background:linear-gradient(90deg,var(--gold),var(--green));
    margin:20px auto 0;border-radius:2px}}
  .hero-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}}
  .hero-card{{background:var(--surface);border:1px solid var(--border);border-radius:16px;
    padding:24px;position:relative;overflow:hidden;transition:transform .2s,border-color .2s;
    animation:fadeUp .5s ease both}}
  .hero-card:hover{{transform:translateY(-3px);border-color:rgba(246,201,14,.3)}}
  .hero-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px}}
  .hero-card.gold::before{{background:var(--gold)}}
  .hero-card.green::before{{background:var(--green)}}
  .hero-card.coral::before{{background:var(--coral)}}
  .hero-card.sky::before{{background:var(--sky)}}
  .hero-card:nth-child(1){{animation-delay:.05s}}
  .hero-card:nth-child(2){{animation-delay:.10s}}
  .hero-card:nth-child(3){{animation-delay:.15s}}
  .hero-card:nth-child(4){{animation-delay:.20s}}
  .hero-icon{{font-size:28px;margin-bottom:12px;display:block}}
  .hero-value{{font-family:'Playfair Display',serif;font-size:38px;font-weight:700;line-height:1;margin-bottom:6px}}
  .hero-card.gold .hero-value{{color:var(--gold)}}
  .hero-card.green .hero-value{{color:var(--green)}}
  .hero-card.coral .hero-value{{color:var(--coral)}}
  .hero-card.sky .hero-value{{color:var(--sky)}}
  .hero-label{{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;font-weight:500}}
  .insights-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:24px}}
  .insight-pill{{background:var(--surface2);border:1px solid var(--border);border-radius:12px;
    padding:16px 20px;display:flex;align-items:flex-start;gap:12px;
    animation:fadeUp .5s .25s ease both}}
  .insight-icon{{font-size:20px;flex-shrink:0;margin-top:2px}}
  .insight-text{{font-size:13px;color:var(--muted);line-height:1.5}}
  .insight-text strong{{color:var(--text);display:block;margin-bottom:2px}}
  .chart-card{{background:var(--surface);border:1px solid var(--border);border-radius:16px;
    padding:28px;animation:fadeUp .5s .3s ease both}}
  .chart-title{{font-family:'Playfair Display',serif;font-size:18px;font-weight:700;margin-bottom:4px}}
  .chart-subtitle{{font-size:12px;color:var(--muted);margin-bottom:22px;font-weight:300}}
  .grid-wide{{display:grid;grid-template-columns:2fr 1fr;gap:20px;margin-bottom:20px}}
  .grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px}}
  .finance-bar{{background:var(--surface2);border-radius:12px;padding:18px 22px;
    margin-bottom:14px;display:flex;align-items:center;gap:24px}}
  .finance-info{{min-width:120px}}
  .finance-label{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:4px}}
  .finance-value{{font-family:'DM Mono',monospace;font-size:22px;font-weight:500}}
  .finance-track{{flex:2}}
  .progress-bg{{background:var(--border);border-radius:99px;height:8px;overflow:hidden;margin-bottom:5px}}
  .progress-fill{{height:100%;border-radius:99px}}
  .progress-label{{font-size:11px;color:var(--muted);font-family:'DM Mono',monospace}}
  .church-list{{list-style:none}}
  .church-item{{display:flex;align-items:center;gap:10px;padding:9px 0;
    border-bottom:1px solid rgba(255,255,255,.04)}}
  .church-item:last-child{{border-bottom:none}}
  .church-rank{{font-family:'DM Mono',monospace;font-size:11px;color:var(--muted);
    width:20px;text-align:right}}
  .church-bar-bg{{flex:1;background:var(--border);border-radius:4px;height:6px;overflow:hidden}}
  .church-bar-fill{{height:100%;border-radius:4px}}
  .church-name{{font-size:13px;font-weight:500;min-width:130px;
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
  .church-count{{font-family:'DM Mono',monospace;font-size:13px;font-weight:500;
    min-width:24px;text-align:right}}
  .badge{{display:inline-flex;align-items:center;gap:5px;font-size:11px;
    padding:4px 10px;border-radius:20px;font-weight:500}}
  .badge.warning{{background:rgba(255,107,107,.15);color:var(--coral);border:1px solid rgba(255,107,107,.2)}}
  .badge.success{{background:rgba(61,220,132,.1);color:var(--green);border:1px solid rgba(61,220,132,.2)}}
  .badge.yellow{{background:rgba(246,201,14,.1);color:var(--gold);border:1px solid rgba(246,201,14,.2)}}
  .timeline-wrap{{display:flex;align-items:flex-end;gap:10px;height:130px;
    margin-top:16px;padding-bottom:32px;position:relative}}
  .tl-col{{flex:1;display:flex;flex-direction:column;align-items:center;
    justify-content:flex-end;height:100%;gap:4px}}
  .tl-num{{font-family:'DM Mono',monospace;font-size:11px}}
  .tl-bar{{width:100%;border-radius:4px 4px 0 0;min-height:4px}}
  .tl-label{{font-size:10px;color:var(--muted);font-family:'DM Mono',monospace;
    margin-top:8px;text-align:center}}
  .tl-grid{{position:absolute;bottom:32px;left:0;right:0;height:1px;
    background:rgba(255,255,255,.05)}}
  .footer{{text-align:center;padding:28px 0 12px;font-size:11px;color:var(--muted);
    font-family:'DM Mono',monospace;border-top:1px solid var(--border);
    margin-top:8px;letter-spacing:1px}}
  @keyframes fadeUp{{from{{opacity:0;transform:translateY(18px)}}to{{opacity:1;transform:translateY(0)}}}}
  @media(max-width:900px){{
    .hero-grid{{grid-template-columns:repeat(2,1fr)}}
    .grid-wide,.grid-2{{grid-template-columns:1fr}}
    .insights-grid{{grid-template-columns:1fr}}
  }}
</style>
</head>
<body>
<div class="container">

  <header class="header">
    <div class="header-badge">📊 Painel de Inscrições</div>
    <h1>ALIVE CAMP</h1>
    <p class="header-sub">12ª Edição · Análise de Inscritos</p>
    <div class="header-line"></div>
  </header>

  <div class="hero-grid">
    <div class="hero-card gold">
      <span class="hero-icon">🏕️</span>
      <div class="hero-value">{total_inscritos}</div>
      <div class="hero-label">Inscrições Confirmadas</div>
    </div>
    <div class="hero-card green">
      <span class="hero-icon">💰</span>
      <div class="hero-value">R${total_pago:,.0f}</div>
      <div class="hero-label">Total Arrecadado</div>
    </div>
    <div class="hero-card coral">
      <span class="hero-icon">⏳</span>
      <div class="hero-value">R${total_falta:,.0f}</div>
      <div class="hero-label">Ainda a Receber</div>
    </div>
    <div class="hero-card sky">
      <span class="hero-icon">⛪</span>
      <div class="hero-value">{total_igrejas}</div>
      <div class="hero-label">Igrejas Representadas</div>
    </div>
  </div>

  <div class="insights-grid">
    <div class="insight-pill">
      <span class="insight-icon">🚨</span>
      <div class="insight-text">
        <strong>Alta inadimplência</strong>
        {round(pendentes/total_inscritos*100) if total_inscritos else 0}% dos inscritos ({pendentes} pessoas) ainda têm saldo em aberto
      </div>
    </div>
    <div class="insight-pill">
      <span class="insight-icon">📅</span>
      <div class="insight-text">
        <strong>Corrida de última hora</strong>
        {ultimos[-1]['label'] if ultimos else '—'} e {ultimos[-2]['label'] if len(ultimos)>1 else '—'} concentram {pct_ultimos}% das inscrições
      </div>
    </div>
    <div class="insight-pill">
      <span class="insight-icon">🏠</span>
      <div class="insight-text">
        <strong>Domínio local</strong>
        {igreja_lider} lidera com {pct_lider}% das inscrições
      </div>
    </div>
  </div>

  <div class="grid-wide">
    <div class="chart-card">
      <div class="chart-title">💵 Situação Financeira</div>
      <div class="chart-subtitle">Arrecadação vs. pendências</div>
      <div class="finance-bar">
        <div class="finance-info">
          <div class="finance-label">Recebido</div>
          <div class="finance-value" style="color:var(--green)">R$ {total_pago:,.0f}</div>
        </div>
        <div class="finance-track">
          <div class="progress-bg"><div class="progress-fill" style="width:{pct_pago}%;background:var(--green)"></div></div>
          <div class="progress-label">{pct_pago}% do total esperado</div>
        </div>
      </div>
      <div class="finance-bar">
        <div class="finance-info">
          <div class="finance-label">A Receber</div>
          <div class="finance-value" style="color:var(--coral)">R$ {total_falta:,.0f}</div>
        </div>
        <div class="finance-track">
          <div class="progress-bg"><div class="progress-fill" style="width:{pct_falta}%;background:var(--coral)"></div></div>
          <div class="progress-label">{pct_falta}% ainda pendente</div>
        </div>
      </div>
      <div class="finance-bar" style="margin-bottom:0">
        <div class="finance-info">
          <div class="finance-label">Total Previsto</div>
          <div class="finance-value" style="color:var(--gold)">R$ {total_previsto:,.0f}</div>
        </div>
        <div class="finance-track">
          <div class="progress-bg"><div class="progress-fill" style="width:100%;background:linear-gradient(90deg,var(--gold),var(--green))"></div></div>
          <div class="progress-label">receita esperada total</div>
        </div>
      </div>
      <div style="margin-top:20px;display:flex;gap:8px;flex-wrap:wrap;">
        <span class="badge success">✓ {quitados} quitados</span>
        <span class="badge warning">⚠ {pendentes} com pendências</span>
      </div>
    </div>

    <div class="chart-card">
      <div class="chart-title">⛪ Ranking de Igrejas</div>
      <div class="chart-subtitle">Inscrições por congregação</div>
      <ul class="church-list">{igrejas_html}</ul>
    </div>
  </div>

  <div class="grid-2">
    <div class="chart-card">
      <div class="chart-title">👥 Faixas Etárias</div>
      <div class="chart-subtitle">Distribuição dos {total_inscritos} inscritos por idade</div>
      <div style="position:relative;width:100%;height:230px;min-height:230px;display:block;-webkit-transform:translateZ(0)">
        <canvas id="chartAge" width="600" height="230" style="display:block;width:100%;height:100%"></canvas>
      </div>
    </div>
    <div class="chart-card">
      <div class="chart-title">💳 Formas de Participação</div>
      <div class="chart-subtitle">Como os inscritos escolheram pagar</div>
      <div style="position:relative;width:100%;height:230px;min-height:230px;display:block;-webkit-transform:translateZ(0)">
        <canvas id="chartPay" width="600" height="230" style="display:block;width:100%;height:100%"></canvas>
      </div>
    </div>
  </div>

  <div class="chart-card" style="margin-bottom:20px">
    <div class="chart-title">📅 Inscrições por Mês</div>
    <div class="chart-subtitle">Evolução temporal das inscrições</div>
    <div class="timeline-wrap">
      {timeline_html}
      <div class="tl-grid"></div>
    </div>
  </div>

  <div class="footer">
    ALIVE CAMP · 12ª EDIÇÃO · {total_inscritos} inscrições confirmadas · Atualizado automaticamente
  </div>

</div>
<script>
var faixasLabels = {json.dumps(faixas_labels)};
var faixasValues = {json.dumps(faixas_values)};
var pagLabels    = {json.dumps(pag_labels)};
var pagValues    = {json.dumps(pag_values)};
var totalInscritos = {total_inscritos};

Chart.defaults.color = '#8b949e';
Chart.defaults.font.family = "'Outfit', sans-serif";

function initCharts() {{
  var canvasAge = document.getElementById('chartAge');
  var canvasPay = document.getElementById('chartPay');
  function sizeCanvas(canvas) {{
    var parent = canvas.parentElement;
    var w = parent.offsetWidth || 300;
    var h = parent.offsetHeight || 230;
    canvas.width  = w * (window.devicePixelRatio || 1);
    canvas.height = h * (window.devicePixelRatio || 1);
    canvas.style.width  = w + 'px';
    canvas.style.height = h + 'px';
  }}
  sizeCanvas(canvasAge);
  sizeCanvas(canvasPay);

  new Chart(canvasAge.getContext('2d'), {{
    type: 'bar',
    data: {{
      labels: faixasLabels,
      datasets: [{{
        data: faixasValues,
        backgroundColor: ['rgba(79,195,247,.7)','rgba(167,139,250,.7)','rgba(61,220,132,.7)','rgba(246,201,14,.8)','rgba(255,107,107,.7)'],
        borderColor:     ['#4fc3f7','#a78bfa','#3ddc84','#f6c90e','#ff6b6b'],
        borderWidth: 1.5, borderRadius: 6
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }}, tooltip: {{ callbacks: {{ label: function(ctx) {{ return ' ' + ctx.raw + ' inscritos'; }} }} }} }},
      scales: {{
        x: {{ grid: {{ color: 'rgba(255,255,255,.04)' }}, ticks: {{ font: {{ size: 11 }}, color: '#8b949e' }} }},
        y: {{ grid: {{ color: 'rgba(255,255,255,.06)' }}, ticks: {{ font: {{ size: 11 }}, color: '#8b949e', stepSize: 5 }}, beginAtZero: true }}
      }}
    }}
  }});

  new Chart(canvasPay.getContext('2d'), {{
    type: 'doughnut',
    data: {{
      labels: pagLabels,
      datasets: [{{
        data: pagValues,
        backgroundColor: ['rgba(246,201,14,.8)','rgba(61,220,132,.75)','rgba(79,195,247,.75)','rgba(167,139,250,.75)','rgba(255,107,107,.75)'],
        borderColor: 'rgba(22,27,34,.8)', borderWidth: 2, hoverOffset: 6
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false, cutout: '62%',
      plugins: {{
        legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }}, color: '#8b949e', padding: 10, boxWidth: 10, boxHeight: 10 }} }},
        tooltip: {{ callbacks: {{ label: function(ctx) {{ return ' ' + ctx.raw + ' inscritos (' + Math.round(ctx.raw/totalInscritos*100) + '%)'; }} }} }}
      }}
    }}
  }});
}}

if (document.readyState === 'loading') {{
  document.addEventListener('DOMContentLoaded', initCharts);
}} else {{
  initCharts();
}}
</script>
</body>
</html>"""

output_path = Path("index.html")
output_path.write_text(html, encoding="utf-8")
print(f"✅ index.html gerado com sucesso! ({total_inscritos} inscritos, R${total_previsto:,.0f} previsto)")
