import os, io, json, textwrap, random, math, datetime
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
# from caas_jupyter_tools import display_dataframe_to_user

from machine_log import df
from maintenance_report import reports

base_dir = os.path.dirname(os.path.abspath(__file__))
out_dir = os.path.join(base_dir, "data")

recent_window = 6
insights = []
for m in df['machine_id'].unique():
    d = df[df['machine_id']==m].copy()
    recent = d.tail(recent_window)
    features = recent[['output_rate','downtime_min','temperature_c']].values
    # Fit IsolationForest on the whole machine history's features to detect outliers in recent window
    model = IsolationForest(contamination=0.03, random_state=42)
    model.fit(d[['output_rate','downtime_min','temperature_c']])
    preds = model.predict(recent[['output_rate','downtime_min','temperature_c']])
    anomaly_count = int((preds==-1).sum())
    avg_output = recent['output_rate'].mean()
    avg_downtime = recent['downtime_min'].mean()
    avg_temp = recent['temperature_c'].mean()
    # Simple rule-based risk score (0-100)
    score = 0
    if avg_output < d['output_rate'].mean()*0.8: score += 40
    if avg_downtime > d['downtime_min'].mean()*3: score += 30
    if avg_temp > d['temperature_c'].mean() + 10: score += 30
    score = min(100, score + anomaly_count*10)
    insights.append({
        "machine": m,
        "recent_avg_output": round(avg_output,1),
        "recent_avg_downtime": round(avg_downtime,1),
        "recent_avg_temp": round(avg_temp,1),
        "anomalies_in_window": anomaly_count,
        "risk_score": score
    })

insights_df = pd.DataFrame(insights).sort_values('risk_score', ascending=False)
insights_path = os.path.join(out_dir, "insights_summary.csv")
insights_df.to_csv(insights_path, index=False)

# 4) Merge with maintenance notes and create human-readable summaries (template-based)
def fetch_note(machine_id):
    for r in reports:
        if r['machine']==machine_id:
            return r['note']
    return ""

summary_rows = []
for _, row in insights_df.iterrows():
    machine = row['machine']
    note = fetch_note(machine)
    # Template summary
    if row['risk_score'] >= 50:
        status = "HIGH RISK — immediate attention recommended"
    elif row['risk_score'] >= 20:
        status = "MEDIUM RISK — investigate soon"
    else:
        status = "LOW RISK — monitor"
    summary = textwrap.dedent(f"""
    Machine {machine} | Risk Score: {row['risk_score']}
    - Recent Avg Output: {row['recent_avg_output']}
    - Recent Avg Downtime (min): {row['recent_avg_downtime']}
    - Recent Avg Temp (C): {row['recent_avg_temp']}
    - Anomalies detected in recent window: {row['anomalies_in_window']}
    - Maintenance Note: {note}
    => Suggested Action: { 'Inspect cooling system & schedule maintenance' if 'heating' in note.lower() or row['recent_avg_temp']>80 else 'Investigate logs; check bearings and PLC' }
    """).strip()
    summary_rows.append({"machine":machine, "summary":summary})

summary_df = pd.DataFrame(summary_rows)
summary_path = os.path.join(out_dir, "human_readable_summaries.csv")
summary_df.to_csv(summary_path, index=False)