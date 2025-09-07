import sys, csv
import matplotlib.pyplot as plt
def main():
    if len(sys.argv)<2: print('Usage: plot_results.py results.csv'); return
    rows=list(csv.DictReader(open(sys.argv[1],encoding='utf-8')))
    rows=[r for r in rows if str(r.get('available','')).lower() in ('1','true','yes')]
    if not rows: print('No available backends in CSV (Phase-1 only requires pyglet_pyopengl).'); return
    names=[r['backend'] for r in rows]; fps=[float(r.get('fps',0) or 0) for r in rows]; init=[float(r.get('init_time_s',0) or 0) for r in rows]
    plt.figure(); plt.bar(names,fps); plt.title('FPS'); plt.ylabel('fps'); plt.savefig('plot_fps.png',dpi=140)
    plt.figure(); plt.bar(names,init); plt.title('Init time (s)'); plt.ylabel('s'); plt.savefig('plot_init.png',dpi=140)
    print('Wrote plot_fps.png, plot_init.png')
if __name__=='__main__': main()
