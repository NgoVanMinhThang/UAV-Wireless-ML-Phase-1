import json, os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
ART='artifacts'; os.makedirs(ART,exist_ok=True); pdf=os.path.join(ART,'phase1_validation_report.pdf')
c=canvas.Canvas(pdf,pagesize=A4); W,H=A4; y=H-2*cm
def line(t,f='Helvetica',s=11):
    global y
    c.setFont(f,s); c.drawString(2*cm,y,t); y-=0.5*cm
c.setTitle('Phase-1 Validation — UAV Wireless‑ML (Slim v3)')
line('UAV Wireless‑ML — Phase‑1 Validation (Slim v3)','Helvetica-Bold',14)
line('Time: '+datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
line('')
line('[PyTest]')
try:
    s=open(os.path.join(ART,'pytest.txt'),encoding='utf-8').read().strip().splitlines()[-1]; line('Summary: '+s)
except Exception:
    line('Summary: (missing)')
line('')
line('[Headless stats]')
try:
    d=json.load(open(os.path.join(ART,'headless_stats.json'),encoding='utf-8'))
    for k in ['time_s','step','enqueued','dequeued','dropped','avg_latency_s','max_latency_s','packets_logged']:
        line(f"{k}: {d.get(k)}")
except Exception as e:
    line('missing: '+repr(e))
line('')
line('[Benchmark]')
try:
    for ln in open(os.path.join(ART,'results_fw_bench.csv'),encoding='utf-8').read().strip().splitlines()[:6]: line(ln)
    if os.path.exists('plot_fps.png'): c.drawImage('plot_fps.png',2*cm,y-7*cm,width=16*cm,height=6*cm); y-=7.2*cm
    if os.path.exists('plot_init.png'): c.drawImage('plot_init.png',2*cm,y-7*cm,width=16*cm,height=6*cm); y-=7.2*cm
except Exception as e:
    line('missing: '+repr(e))
c.showPage(); c.save(); print('Wrote', pdf)
