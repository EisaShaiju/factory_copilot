base_dir = os.path.dirname(os.path.abspath(__file__))
out_dir = os.path.join(base_dir, "data")
reports = [
    {"machine":"M1","note":"All good. Routine lubrication performed yesterday. No overheating observed."},
    {"machine":"M2","note":"Vibration noted on bearing B2 last week; monitored, no action taken."},
    {"machine":"M3","note":"Operator logs: 'Machine 3 showing heating since Monday; increased idle time.' Technical team to inspect cooling."},
    {"machine":"M4","note":"Minor electrical hiccups observed; reset PLC on Friday."},
]
txt_path = os.path.join(out_dir, "maintenance_reports.txt")
with open(txt_path,'w') as f:
    for r in reports:
        f.write(f"---\nMACHINE: {r['machine']}\n{r['note']}\n\n")