"""Simple Streamlit front end for the governed credit-risk engine."""
import pandas as pd
import streamlit as st
from pathlib import Path
from src.governance import has_permission, validate_macro_scenarios

ROOT = Path(__file__).resolve().parent
AUDIT = ROOT / "outputs" / "borrower_audit_trace.csv"
MACRO = ROOT / "config" / "macro_scenarios.csv"

st.set_page_config(page_title="SME Credit Risk Platform", layout="wide")
st.title("SME Credit Risk Platform")
st.caption("PD • EWS • IFRS 9-style staging • ECL • governed interventions")

role = st.sidebar.selectbox("Demo role", ["Credit Analyst","Risk Manager","Model Validation","Auditor","Admin"])
st.sidebar.info("Portfolio demo RBAC — not production authentication.")

if not AUDIT.exists():
    st.error("Run the credit-risk pipeline first to generate borrower_audit_trace.csv.")
    st.stop()
df = pd.read_csv(AUDIT)

tabs = st.tabs(["Portfolio","Borrower 360","Overrides","Macro Scenarios","Admin / Audit"])

with tabs[0]:
    a,b,c,d = st.columns(4)
    a.metric("Borrowers", f"{len(df):,}")
    b.metric("Mean PD", f"{df.predicted_pd.mean():.2%}")
    c.metric("Total EAD", f"€{df.ead.sum()/1e6:,.1f}m")
    d.metric("Total ECL", f"€{df.ecl.sum()/1e6:,.1f}m")
    st.dataframe(df.groupby("stage").agg(customers=("customer_id","count"),EAD=("ead","sum"),ECL=("ecl","sum")), use_container_width=True)

with tabs[1]:
    cid = st.selectbox("Customer", df.customer_id.astype(str).tolist())
    x = df[df.customer_id.astype(str).eq(cid)].iloc[0]
    a,b,c,d,e = st.columns(5)
    a.metric("PD", f"{x.predicted_pd:.2%}")
    b.metric("Score", f"{x.credit_score:.0f}")
    c.metric("Risk band", str(x.risk_band))
    d.metric("Stage", str(x.stage))
    e.metric("ECL", f"€{x.ecl:,.0f}")
    st.subheader("Exposure & recovery")
    st.dataframe(pd.DataFrame({"Metric":["Loan EAD","OVD EAD","Trade EAD","Total EAD","Collateral","LGD"],
                               "Value":[x.loan_ead,x.ovd_ead,x.trade_ead,x.ead,x.collateral_value,x.lgd]}), hide_index=True)
    st.subheader("Risk signals")
    cols=[c for c in ["days_past_due","credit_utilization","delinquencies_12m","previous_defaults","months_on_ews_watchlist","risk_direction","current_credit_impaired"] if c in df.columns]
    st.dataframe(pd.DataFrame({"Field":cols,"Value":[x[c] for c in cols]}), hide_index=True)

with tabs[2]:
    st.subheader("Manual intervention")
    st.write("Model output is preserved. Overrides are separate governed decisions.")
    if has_permission(role,"propose_override"):
        typ=st.selectbox("Override type",["PD","Risk band","Stage / SICR","Watchlist","Collateral / recovery"])
        proposed=st.text_input("Proposed value")
        reason=st.selectbox("Reason",["Qualitative risk","New information","Data correction","Credit committee judgement","Other"])
        rationale=st.text_area("Rationale")
        st.button("Submit for approval", disabled=not(proposed and rationale))
    else:
        st.info("Your role is read-only for overrides.")
    if has_permission(role,"approve_override"):
        st.caption("Risk Manager: approval queue enabled (maker-checker control).")

with tabs[3]:
    scenarios=pd.read_csv(MACRO)
    st.dataframe(scenarios,use_container_width=True)
    if has_permission(role,"manage_macro"):
        st.success("Authorized to prepare macro scenario amendments.")
        edited=st.data_editor(scenarios,use_container_width=True,num_rows="fixed")
        if st.button("Validate scenario set"):
            try:
                validate_macro_scenarios(edited)
                st.success("Valid: scenario weights sum to 100%.")
            except ValueError as e:
                st.error(str(e))
    else:
        st.info("Scenario assumptions are read-only for this role.")

with tabs[4]:
    st.subheader("Access & governance")
    st.write(f"Current demo role: **{role}**")
    perms=["view_borrower","run_assessment","propose_override","approve_override","manage_policy","manage_macro","manage_users","view_audit"]
    st.dataframe(pd.DataFrame({"Permission":perms,"Allowed":[has_permission(role,p) for p in perms]}),hide_index=True)
    st.caption("Production deployment would connect this layer to enterprise IAM and a transactional audit store.")
