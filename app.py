import streamlit as st
import pandas as pd
import os
from sklearn.ensemble import IsolationForest

base_dir = os.path.dirname(os.path.abspath(__file__))
out_dir = os.path.join(base_dir, "data")
csv_path = os.path.join(out_dir, "machine_log.csv")
txt_path = os.path.join(out_dir, "maintenance report.txt")

st.set_page_config(layout="wide", page_title="Factory Insight Copilot (Prototype)")
st.title("Factory Insight Copilot — Prototype")
st.markdown("A simple prototype that ingests machine logs + maintenance notes, runs anomaly detection, and outputs human-readable insights.")

@st.cache_data
def load_data(path):
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def load_reports(path):
    if not os.path.exists(path):
        return []
    text = open(path, 'r', encoding='utf-8').read()
    reports = []
    for block in text.split('---'):
        block = block.strip()
        if not block:
            continue
        lines = block.splitlines()
        header = lines[0].strip()
        if header.startswith('MACHINE:'):
            machine = header.split(':',1)[1].strip()
            note = '\n'.join(lines[1:]).strip()
            reports.append({'machine': machine, 'note': note})
    return reports

df = load_data(csv_path)
if df is None:
    st.error(f"Data file not found: {csv_path}. Run `machine_log.py` first to generate sample data.")
    st.stop()

machines = df['machine_id'].unique().tolist()
sel = st.sidebar.multiselect("Select machines", machines, default=machines)

st.subheader('Machine log (tail)')
st.dataframe(df[df['machine_id'].isin(sel)].tail(20))

reports = load_reports(txt_path)
reports_by_machine = {r['machine']: r['note'] for r in reports}

def analyze(df, machines_to_run):
    insights = []
    summaries = []
    for m in machines_to_run:
        d = df[df['machine_id'] == m].copy()
        if d.empty:
            continue
        recent = d.tail(6)
        model = IsolationForest(contamination=0.03, random_state=42)
        # fit on historical data
        model.fit(d[['output_rate','downtime_min','temperature_c']])
        preds = model.predict(recent[['output_rate','downtime_min','temperature_c']])
        anomaly_count = int((preds == -1).sum())
        avg_output = recent['output_rate'].mean()
        avg_downtime = recent['downtime_min'].mean()
        avg_temp = recent['temperature_c'].mean()
        score = 0
        if avg_output < d['output_rate'].mean() * 0.8:
            score += 40
        if avg_downtime > d['downtime_min'].mean() * 3:
            score += 30
        if avg_temp > d['temperature_c'].mean() + 10:
            score += 30
        score = min(100, score + anomaly_count * 10)
        note = reports_by_machine.get(m, "")
        insights.append({
            'machine': m,
            'recent_avg_output': round(avg_output,1),
            'recent_avg_downtime': round(avg_downtime,1),
            'recent_avg_temp': round(avg_temp,1),
            'anomalies_in_window': int(anomaly_count),
            'risk_score': int(score)
        })
        status = "HIGH RISK — immediate attention recommended" if score >= 50 else ("MEDIUM RISK — investigate soon" if score >= 20 else "LOW RISK — monitor")
        suggested = "Inspect cooling system & schedule maintenance" if 'heat' in note.lower() or avg_temp > 80 else "Investigate logs; check bearings and PLC"
        summary_text = f"Machine {m} | Risk Score: {score}\n- Recent Avg Output: {round(avg_output,1)}\n- Recent Avg Downtime (min): {round(avg_downtime,1)}\n- Recent Avg Temp (C): {round(avg_temp,1)}\n- Anomalies detected in recent window: {anomaly_count}\n- Maintenance Note: {note}\n=> Suggested Action: {suggested}"
        summaries.append({'machine': m, 'summary': summary_text})
    return pd.DataFrame(insights), pd.DataFrame(summaries)

if st.sidebar.button('Detect Anomalies & Summarize'):
    with st.spinner('Running analysis...'):
        insights_df, summary_df = analyze(df, sel)
    st.subheader('Insights')
    st.dataframe(insights_df.sort_values('risk_score', ascending=False))
    st.subheader('Human-readable summaries')
    for _, row in summary_df.iterrows():
        st.markdown(f"**{row['machine']}**")
        st.text(row['summary'])

st.sidebar.markdown('### Files in data/')
if os.path.exists(out_dir):
    for f in sorted(os.listdir(out_dir)):
        st.sidebar.write(f)

