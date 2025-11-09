import os, io, json, textwrap, random, math, datetime
import pandas as pd
import numpy as np
# from sklearn.ensemble import IsolationForest
# from caas_jupyter_tools import display_dataframe_to_user

base_dir = os.path.dirname(os.path.abspath(__file__))
out_dir = os.path.join(base_dir, "data")
os.makedirs(out_dir, exist_ok=True)

# 1) Generate machine_log.csv
np.random.seed(42)
machines = ["M1", "M2", "M3", "M4"]
start = datetime.datetime.now() - datetime.timedelta(hours=48)
rows = []
for m in machines:
    # baseline params per machine
    base_output = random.randint(80, 120)
    base_temp = random.uniform(55, 75)
    for i in range(96):  # 48 hours, 30-min intervals
        ts = start + datetime.timedelta(minutes=30*i)
        # Introduce slight drift and noise
        drift = (i/96) * random.uniform(-5, 5)
        # normal behaviour
        output_rate = max(0, int(np.random.normal(base_output + drift, 5)))
        downtime = max(0, int(np.random.exponential(0.2)))  # minutes
        temp = base_temp + np.random.normal(0, 1.2) + (0.02*i if m=="M3" and i>60 else 0)  # M3 may overheat later
        error_code = 0 if random.random() > 0.02 else random.choice([101,102,201])
        rows.append([m, ts.strftime("%Y-%m-%d %H:%M:%S"), output_rate, downtime, round(temp,2), error_code])

# Insert an injected anomaly for M3: extended downtime and output drop in last 6 intervals
for k in range(6):
    rows.append(["M3", (start + datetime.timedelta(minutes=30*(90+k))).strftime("%Y-%m-%d %H:%M:%S"),
                 int(20 + np.random.normal(0,2)),  # severe drop in output
                 30 + int(np.random.exponential(5)),  # large downtime
                 round(95 + np.random.normal(0,1),2),  # high temp
                 501])

df = pd.DataFrame(rows, columns=["machine_id","timestamp","output_rate","downtime_min","temperature_c","error_code"])
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values(['machine_id','timestamp']).reset_index(drop=True)

csv_path = os.path.join(out_dir, "machine_log.csv")
df.to_csv(csv_path, index=False)