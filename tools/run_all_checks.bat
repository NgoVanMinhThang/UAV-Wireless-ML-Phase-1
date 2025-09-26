@echo off
REM Run pytest
python -m pytest -q > artifacts\pytest.txt

REM Run headless simulation
python cli.py --config configs\default.yaml --steps 500 --headless > artifacts\headless_stats.json

REM Run framework benchmark
python -m benchmarks.fw_bench --duration 5 --csv artifacts\results_fw_bench.csv

REM Plot results
python benchmarks\plot_results.py artifacts\results_fw_bench.csv

REM Write PDF report
python tools\write_report_pdf.py

echo Done. See artifacts\
