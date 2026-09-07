import streamlit as st
import pandas as pd
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]/"src"))

st.set_page_config(page_title="Credit Risk Dashboard",layout="wide")
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/"data/processed/scored_portfolio.csv"

st.title("SME Credit Risk Analytics Dashboard")
if not p.exists():
    st.warning("Run `python notebooks/credit_risk_pipeline.py` first.")
    st.stop()

df=pd.read_csv(p)
c1,c2,c3,c4=st.columns(4)
c1.metric("Customers",f"{len(df):,}")
c2.metric("Default Rate",f"{df.default.mean():.2%}")
c3.metric("Exposure",f"€{df.ead.sum()/1e6:.1f}M")
c4.metric("12M ECL",f"€{df.ecl_12m.sum()/1e6:.2f}M")

st.subheader("Risk Segmentation")
seg=df.groupby("risk_band").agg(Customers=("customer_id","count"),
                                Default_Rate=("default","mean"),
                                Exposure=("ead","sum"),
                                ECL=("ecl_12m","sum")).reset_index()
st.dataframe(seg.style.format({"Default_Rate":"{:.2%}","Exposure":"€{:,.0f}","ECL":"€{:,.0f}"}),use_container_width=True)

st.subheader("Industry Risk")
ind=df.groupby("industry").agg(Customers=("customer_id","count"),
                                Default_Rate=("default","mean"),
                                Exposure=("ead","sum"),
                                ECL=("ecl_12m","sum")).sort_values("Default_Rate",ascending=False)
st.bar_chart(ind["Default_Rate"])
st.dataframe(ind.style.format({"Default_Rate":"{:.2%}","Exposure":"€{:,.0f}","ECL":"€{:,.0f}"}),use_container_width=True)

st.subheader("Borrower Scoring")
bands=st.multiselect("Risk band",df.risk_band.unique(),default=list(df.risk_band.unique()))
view=df[df.risk_band.isin(bands)][["customer_id","industry","loan_amount","predicted_pd","credit_score","risk_band","ead","lgd","ecl_12m"]]
st.dataframe(view.head(200).style.format({"loan_amount":"€{:,.0f}","predicted_pd":"{:.2%}",
                                           "credit_score":"{:.0f}","ead":"€{:,.0f}","lgd":"{:.1%}","ecl_12m":"€{:,.0f}"}),use_container_width=True)
