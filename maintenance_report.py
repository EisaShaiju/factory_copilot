import os, io, json, textwrap, random, math, datetime
import pandas as pd
import numpy as np

base_dir = os.path.dirname(os.path.abspath(__file__))
out_dir = os.path.join(base_dir, "data")
os.makedirs(out_dir, exist_ok=True)

reports = [
    {"machine":"M1","note":"All good. Routine lubrication performed yesterday. No overheating observed."},
    {"machine":"M2","note":"Vibration noted on bearing B2 last week; monitored, no action taken."},
    {"machine":"M3","note":"Operator logs: 'Machine 3 showing heating since Monday; increased idle time.' Technical team to inspect cooling."},
    {"machine":"M4","note":"Minor electrical hiccups observed; reset PLC on Friday."},
]
txt_path = os.path.join(out_dir, "maintenance report.txt")
with open(txt_path, 'w', encoding='utf-8') as f:
    for r in reports:
        f.write(f"---\nMACHINE: {r['machine']}\n{r['note']}\n\n")