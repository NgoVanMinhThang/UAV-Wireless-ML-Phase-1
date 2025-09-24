@echo off
setlocal
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
if not exist artifacts mkdir artifacts
%PY% -m pytest -q > artifacts\pytest.txt
%PY% cli.py --config configs\default.yaml --steps 600 --headless > artifacts\headless_stats.json
%PY% -m benchmarks.fw_bench --duration 8 --n_uav 5 --n_ue 300 --csv artifacts\results_fw_bench.csv
%PY% benchmarks\plot_results.py artifacts\results_fw_bench.csv
%PY% tools\write_report_pdf.py
echo Done. See artifacts\
endlocal
