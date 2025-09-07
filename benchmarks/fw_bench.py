import os, sys, importlib, csv, argparse, traceback
if __package__ is None or __package__ == "":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    __package__ = "benchmarks"
BACKENDS=["pyglet_pyopengl"]
def _load_backend(name):
    try: return importlib.import_module(f".fw_backends.{name}", package=__package__)
    except Exception: return importlib.import_module(f"benchmarks.fw_backends.{name}")
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--duration',type=float,default=8.0)
    ap.add_argument('--n_uav',type=int,default=5)
    ap.add_argument('--n_ue',type=int,default=300)
    ap.add_argument('--csv',default='results_fw_bench.csv')
    args=ap.parse_args()
    rows=[]
    for name in BACKENDS:
        try:
            m=_load_backend(name); res=m.run(duration_s=args.duration,n_uav=args.n_uav,n_ue=args.n_ue)
            res.setdefault('backend',name); res.setdefault('available',True)
        except Exception as e:
            res={'backend':name,'available':False,'error':repr(e),'trace':''.join(tr for tr in traceback.format_exc().splitlines()[-6:])}
        rows.append(res); print(res)
    keys=sorted({k for r in rows for k in r.keys()})
    with open(args.csv,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)
    print('Wrote',args.csv)
if __name__=='__main__': main()
