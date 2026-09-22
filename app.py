"""Simple Streamlit front end for the governed credit-risk engine."""
import pandas as pd
import streamlit as st
from pathlib import Path
from src.governance import has_permission, validate_macro_scenarios, OverrideRequest, approve_override, append_audit_event

ROOT = Path(__file__).resolve().parent
AUDIT = ROOT / "outputs" / "borrower_audit_trace.csv"
MACRO = ROOT / "config" / "macro_scenarios.csv"
AUDIT_LOG = ROOT / "outputs" / "governance_audit.jsonl"

st.set_page_config(page_title="SME Credit Risk Platform", layout="wide")
st.title("SME Credit Risk Platform")
st.caption("PD • EWS • IFRS 9-style staging • ECL • governed interventions")

user = st.sidebar.text_input("User", value="demo.user")
role = st.sidebar.selectbox("Role", ["Credit Analyst","Risk Manager","Model Validation","Auditor","Admin"])
st.sidebar.info("Portfolio demo RBAC — not production authentication.")

if not AUDIT.exists():
    st.error("Run the credit-risk pipeline first to generate borrower_audit_trace.csv.")
    st.stop()
df = pd.read_csv(AUDIT)

page = st.sidebar.radio("Workspace", ["Portfolio Cockpit","Borrower Credit File","Risk Management"])

# Three task-oriented workspaces keep the demo focused.
tabs = st.tabs(["Portfolio Cockpit","Borrower Credit File","Risk Management"])

with tabs[0]:
    st.subheader("Portfolio Cockpit")
    st.caption("Identify concentration, deterioration and loss contributors before opening a case.")
    a,b,c,d = st.columns(4)
    a.metric("Borrowers", f"{len(df):,}")
    b.metric("Mean PD", f"{df.predicted_pd.mean():.2%}")
    c.metric("Total EAD", f"€{df.ead.sum()/1e6:,.1f}m")
    d.metric("Total ECL", f"€{df.ecl.sum()/1e6:,.1f}m")
    stage_view=df.groupby("stage").agg(customers=("customer_id","count"),EAD=("ead","sum"),ECL=("ecl","sum")).reset_index()
    stage_view["EAD"]=stage_view["EAD"].map(lambda v:f"€{v/1e6:,.2f}m")
    stage_view["ECL"]=stage_view["ECL"].map(lambda v:f"€{v/1e6:,.2f}m")
    st.dataframe(stage_view,hide_index=True,use_container_width=True)
    st.markdown("#### Highest-priority cases")
    priority=df.copy()
    priority["_priority"]=priority["ecl"].rank(pct=True)+priority["predicted_pd"].rank(pct=True)
    if "risk_direction" in priority.columns:
        priority["_priority"]+=priority["risk_direction"].eq("Deteriorating").astype(int)
    case_cols=[x for x in ["customer_id","industry","predicted_pd","credit_score","risk_band","risk_direction","stage","days_past_due","ead","ecl"] if x in priority.columns]
    cases=priority.nlargest(12,"_priority")[case_cols].copy()
    if "predicted_pd" in cases: cases["predicted_pd"]=cases["predicted_pd"].map(lambda v:f"{v:.2%}")
    for money in ["ead","ecl"]:
        if money in cases: cases[money]=cases[money].map(lambda v:f"€{v:,.0f}")
    st.dataframe(cases,hide_index=True,use_container_width=True)

with tabs[1]:
    st.subheader("Borrower Credit File")
    st.caption("One place to understand model risk, behaviour, exposure, staging and expected loss.")
    cid = st.selectbox("Customer", df.customer_id.astype(str).tolist())
    x = df[df.customer_id.astype(str).eq(cid)].iloc[0]
    a,b,c,d,e = st.columns(5)
    a.metric("PD", f"{x.predicted_pd:.2%}")
    b.metric("Score", f"{x.credit_score:.0f}")
    c.metric("Risk band", str(x.risk_band))
    d.metric("Stage", str(x.stage))
    e.metric("ECL", f"€{x.ecl:,.0f}")
    st.markdown("#### Decision summary")
    ews=str(x["risk_direction"]) if "risk_direction" in df.columns else "—"
    st.write(f"**{x.risk_band}** model risk · **{ews}** EWS · **{x.stage}** accounting classification. "
             f"Exposure is **€{x.ead:,.0f}** with expected loss of **€{x.ecl:,.0f}**.")
    st.subheader("Exposure & recovery")
    st.dataframe(pd.DataFrame({"Metric":["Loan EAD","OVD EAD","Trade EAD","Total EAD","Collateral","LGD"],
                               "Value":[x.loan_ead,x.ovd_ead,x.trade_ead,x.ead,x.collateral_value,x.lgd]}), hide_index=True)
    st.subheader("Credit interpretation")
    adverse=[]
    if "leverage_ratio" in df.columns and x.leverage_ratio >= 3: adverse.append(f"leverage {x.leverage_ratio:.1f}x")
    if "credit_utilization" in df.columns and x.credit_utilization >= .8: adverse.append(f"utilization {x.credit_utilization:.1%}")
    if "delinquencies_12m" in df.columns and x.delinquencies_12m > 0: adverse.append(f"{int(x.delinquencies_12m)} delinquency event(s)")
    if "days_past_due" in df.columns and x.days_past_due > 0: adverse.append(f"{int(x.days_past_due)} DPD")
    if adverse: st.warning("Key adverse indicators: " + ", ".join(adverse) + ".")
    else: st.success("No major rule-based adverse indicator is elevated in the current snapshot.")
    if "forward_looking_pd_12m" in df.columns:
        st.write(f"Model PD **{x.predicted_pd:.2%}** → macro-adjusted 12M PD **{x.forward_looking_pd_12m:.2%}**. Accounting stage remains a separate decision dimension.")
    st.subheader("Risk signals")
    cols=[c for c in ["days_past_due","credit_utilization","delinquencies_12m","previous_defaults","consecutive_ews_months","risk_direction","current_credit_impaired"] if c in df.columns]
    st.dataframe(pd.DataFrame({"Field":cols,"Value":[x[c] for c in cols]}), hide_index=True)

with tabs[2]:
    st.subheader("Manual intervention")
    st.write("Model output is preserved. Overrides are separate governed decisions.")
    if has_permission(role,"propose_override"):
        typ=st.selectbox("Override type",["PD","Risk band","Stage / SICR","Watchlist","Collateral / recovery"])
        proposed=st.text_input("Proposed value")
        reason=st.selectbox("Reason",["Qualitative risk","New information","Data correction","Credit committee judgement","Other"])
        rationale=st.text_area("Rationale")
        if st.button("Submit for approval", disabled=not(proposed and rationale)):
            req = OverrideRequest(str(cid), typ, str(x.predicted_pd if typ=="PD" else x.risk_band), proposed, reason.upper().replace(" ","_"), rationale, user, role)
            try:
                req.validate()
                st.session_state["pending_override"] = req
                append_audit_event(AUDIT_LOG, {"actor":user,"role":role,"action":"PROPOSE_OVERRIDE","customer_id":str(cid),"override_type":typ,"proposed_value":proposed,"reason":reason})
                st.success("Submitted for Risk Manager approval.")
            except (ValueError, PermissionError) as e:
                st.error(str(e))
    else:
        st.info("Your role is read-only for overrides.")
    if has_permission(role,"approve_override"):
        st.caption("Risk Manager approval queue")
        req = st.session_state.get("pending_override")
        if req:
            st.write(f"**{req.customer_id}** · {req.override_type}: {req.model_value} → **{req.proposed_value}**")
            st.caption(f"{req.reason_code} — {req.rationale}")
            if st.button("Approve override"):
                try:
                    approved = approve_override(req, user, role)
                    append_audit_event(AUDIT_LOG, {"actor":user,"role":role,"action":"APPROVE_OVERRIDE","customer_id":req.customer_id,"override_type":req.override_type,"proposed_value":req.proposed_value})
                    st.session_state["last_approved_override"] = approved
                    del st.session_state["pending_override"]
                    st.success("Override approved and audit event recorded.")
                    st.rerun()
                except PermissionError as e:
                    st.error(str(e))
        else:
            st.info("No override waiting for approval.")


    st.markdown("#### Macro scenarios")
    scenarios=pd.read_csv(MACRO)
    st.dataframe(scenarios,use_container_width=True)
    if {"pit_pd_12m","forward_looking_pd_12m"}.issubset(df.columns):
        base=(df.pit_pd_12m*df.lgd*df.ead).sum()
        fwd=(df.forward_looking_pd_12m*df.lgd*df.ead).sum()
        m1,m2,m3=st.columns(3)
        m1.metric("PIT 12M diagnostic ECL",f"€{base/1e6:,.2f}m")
        m2.metric("Forward-looking 12M ECL",f"€{fwd/1e6:,.2f}m")
        m3.metric("Macro overlay impact",f"€{(fwd-base)/1e6:,.2f}m")
    if has_permission(role,"manage_macro"):
        edited=st.data_editor(scenarios,use_container_width=True,num_rows="fixed")
        if st.button("Validate proposed scenarios"):
            try:
                validate_macro_scenarios(edited); st.success("Valid scenario set: weights sum to 100%.")
            except ValueError as e: st.error(str(e))
    else: st.info("Macro assumptions are read-only for this role.")

    st.markdown("#### Governance")
    st.info("Validated model coefficients are read-only. Policy, macro assumptions and human overrides are governed separately.")
    perms=["view_borrower","run_assessment","propose_override","approve_override","manage_policy","manage_macro","manage_users","view_audit"]
    st.dataframe(pd.DataFrame({"Permission":perms,"Allowed":[has_permission(role,p) for p in perms]}),hide_index=True)
