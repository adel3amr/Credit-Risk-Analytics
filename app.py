"""Simple Streamlit front end for the governed credit-risk engine."""
import pandas as pd
import streamlit as st
from pathlib import Path
from src.governance import has_permission, validate_macro_scenarios, OverrideRequest, approve_override, append_audit_event

ROOT = Path(__file__).resolve().parent
AUDIT = ROOT / "outputs" / "borrower_audit_trace.csv"
MACRO = ROOT / "config" / "macro_scenarios.csv"
AUDIT_LOG = ROOT / "outputs" / "governance_audit.jsonl"
MODEL_VALIDATION = ROOT / "outputs" / "model_validation.csv"
CALIBRATION = ROOT / "outputs" / "calibration_deciles.csv"
LGD_VALIDATION = ROOT / "outputs" / "lgd_model_validation.csv"
LGD_CALIBRATION = ROOT / "outputs" / "lgd_calibration_deciles.csv"
FACILITY_LGD = ROOT / "outputs" / "facility_lgd_predictions.csv"
FACILITY_ECL = ROOT / "outputs" / "facility_ecl_predictions.csv"

st.set_page_config(page_title="Credit Risk Analytics — V5", layout="wide")
st.title("Credit Risk Analytics & IFRS 9 Decisioning System — V5")
st.caption("PD • LGD • EWS • IFRS 9-style staging • ECL • governed interventions")

def pct(v, decimals=2):
    return f"{float(v):.{decimals}%}"

def format_money(v):
    return f"€{float(v):,.2f}"

def compact_money(v):
    """Compact display for portfolio headline KPIs only."""
    value = float(v)
    if abs(value) >= 1_000_000_000:
        return f"€{value / 1_000_000_000:.2f}bn"
    if abs(value) >= 1_000_000:
        return f"€{value / 1_000_000:.2f}m"
    return format_money(value)

DEMO_IDENTITIES = {
    "analyst.demo": "Credit Analyst",
    "risk.manager.demo": "Risk Manager",
    "validator.demo": "Model Validation",
    "auditor.demo": "Auditor",
    "admin.demo": "Admin",
}
user = st.sidebar.selectbox("Demo identity", list(DEMO_IDENTITIES))
role = DEMO_IDENTITIES[user]
st.sidebar.caption(f"Role: {role}")
st.sidebar.info("Demo RBAC with fixed identities — not production authentication.")

if not AUDIT.exists():
    st.error("Run the credit-risk pipeline first to generate borrower_audit_trace.csv.")
    st.stop()
df = pd.read_csv(AUDIT)

# Three task-oriented workspaces keep the demo focused.
tab_names = ["Portfolio Cockpit","Borrower Credit File","Risk Management"]
if role == "Model Validation":
    tab_names.append("Model Validation")
tabs = st.tabs(tab_names)

with tabs[0]:
    st.subheader("Portfolio Intelligence & Assessment")
    st.caption("Automated portfolio diagnostics for credit officers. Findings are descriptive review signals, not automatic credit decisions.")

    st.download_button(
        "Download full portfolio CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="sme_credit_risk_portfolio.csv",
        mime="text/csv",
        width="content",
    )

    # Portfolio exposure architecture: loans and OVD are direct; trade instruments are
    # reported separately as contingent/indirect exposure. EAD is kept distinct from
    # nominal facility amounts so CCF treatment remains visible.
    direct_ead = df["loan_ead"].sum() + df["ovd_ead"].sum()
    indirect_nominal = df["trade"].sum()
    indirect_ead = df["trade_ead"].sum()
    total_ead = df["ead"].sum()
    total_ecl = df["ecl"].sum()
    unsecured = df["unsecured_ead"].sum() if "unsecured_ead" in df.columns else 0.0

    a,b,c1,d,e = st.columns(5)
    a.metric("Borrowers", f"{len(df):,}")
    b.metric("Mean PD", pct(df["predicted_pd"].mean()))
    c1.metric("Total EAD", compact_money(total_ead))
    d.metric("Total ECL", compact_money(total_ecl))
    e.metric("Unsecured EAD", compact_money(unsecured))

    st.markdown("#### Portfolio composition")
    p1,p2,p3,p4 = st.columns(4)
    p1.metric("Direct EAD", compact_money(direct_ead))
    p2.metric("Indirect / Trade EAD", compact_money(indirect_ead))
    p3.metric("Nominal trade facilities", compact_money(indirect_nominal))
    p4.metric("ECL / EAD", pct(total_ecl / max(total_ead, 1)))

    has_loan = df["loans"].gt(0)
    has_ovd = df["ovd"].gt(0)
    has_trade = df["trade"].gt(0)
    product_view = pd.DataFrame({
        "Portfolio segment": ["Loans only","OVD only","Trade only","Mixed products"],
        "Borrowers": [
            (has_loan & ~has_ovd & ~has_trade).sum(),
            (~has_loan & has_ovd & ~has_trade).sum(),
            (~has_loan & ~has_ovd & has_trade).sum(),
            ((has_loan.astype(int)+has_ovd.astype(int)+has_trade.astype(int)) >= 2).sum(),
        ],
    })
    st.dataframe(product_view, hide_index=True, width="stretch")

    st.markdown("#### Facility utilization")
    direct_limit = df["direct_limit"].sum()
    direct_drawn = df["direct_drawn"].sum()
    indirect_limit = df["indirect_limit"].sum()
    total_limit = df["total_credit_limit"].sum()
    total_utilized = df["total_utilized_amount"].sum()
    u1,u2,u3,u4 = st.columns(4)
    u1.metric("Total credit limits", compact_money(total_limit))
    u2.metric("Direct utilization", pct(direct_drawn / max(direct_limit, 1)))
    u3.metric("Indirect utilization", pct(indirect_nominal / max(indirect_limit, 1)))
    u4.metric("Total portfolio utilization", pct(total_utilized / max(total_limit, 1)))
    util_view = pd.DataFrame([
        ["Direct — term loan + OVD", direct_limit, direct_drawn, direct_drawn / max(direct_limit,1)],
        ["Indirect — trade", indirect_limit, indirect_nominal, indirect_nominal / max(indirect_limit,1)],
        ["Total", total_limit, total_utilized, total_utilized / max(total_limit,1)],
    ], columns=["Facility class","Approved limit","Utilized / issued amount","Utilization"])
    util_view["Approved limit"]=util_view["Approved limit"].map(format_money)
    util_view["Utilized / issued amount"]=util_view["Utilized / issued amount"].map(format_money)
    util_view["Utilization"]=util_view["Utilization"].map(pct)
    st.dataframe(util_view, hide_index=True, width="stretch")
    st.caption("Direct utilization uses current term-loan outstanding plus OVD drawn amount against approved direct limits. Trade utilization is issued nominal trade facilities against approved indirect limits; CCF-adjusted trade EAD remains a separate credit-risk exposure measure.")

    st.markdown("#### Industry assessment")
    industry = (
        df.groupby("industry")
        .agg(
            Borrowers=("customer_id","count"),
            EAD=("ead","sum"),
            ECL=("ecl","sum"),
            Mean_PD=("predicted_pd","mean"),
            Mean_LGD=("lgd","mean"),
            Stage_2_3=("stage", lambda s: s.isin(["Stage 2","Stage 3"]).mean()),
        )
        .reset_index()
    )
    industry["Exposure_share"] = industry["EAD"] / max(total_ead, 1)
    industry["ECL_share"] = industry["ECL"] / max(total_ecl, 1)
    industry["Loss_intensity"] = industry["ECL"] / industry["EAD"].clip(lower=1)
    industry = industry.sort_values("ECL_share", ascending=False)
    industry_display=industry.copy()
    for col in ["Mean_PD","Mean_LGD","Stage_2_3","Exposure_share","ECL_share","Loss_intensity"]:
        industry_display[col]=industry_display[col].map(pct)
    for col in ["EAD","ECL"]:
        industry_display[col]=industry_display[col].map(format_money)
    st.dataframe(industry_display, hide_index=True, width="stretch")

    st.markdown("#### Data-driven risk patterns")
    # Broad, pre-defined monitoring cuts only. No decision-tree fitting or threshold
    # search is performed on the holdout, avoiding a tight rule set tailored to this sample.
    portfolio_pd = df["predicted_pd"].mean()
    portfolio_loss = total_ecl / max(total_ead, 1)
    patterns = []
    checks = [
        ("High utilization", df["credit_utilization"] >= .80),
        ("Recent delinquency", df["delinquencies_12m"] > 0),
        ("Previous default", df["previous_defaults"] > 0),
        ("Deteriorating EWS", df["risk_direction"].eq("Deteriorating")),
        ("Unsecured", df["recognized_collateral_coverage"] <= .01),
        ("High utilization + deterioration", (df["credit_utilization"] >= .80) & df["risk_direction"].eq("Deteriorating")),
    ]
    min_group = max(30, int(len(df) * .01))
    for label, mask in checks:
        g=df.loc[mask]
        if len(g) < min_group:
            continue
        patterns.append({
            "Pattern": label,
            "Borrowers": len(g),
            "EAD": g["ead"].sum(),
            "Mean PD": g["predicted_pd"].mean(),
            "PD vs portfolio": g["predicted_pd"].mean() / max(portfolio_pd, 1e-9),
            "ECL / EAD": g["ecl"].sum() / max(g["ead"].sum(), 1),
            "Loss vs portfolio": (g["ecl"].sum() / max(g["ead"].sum(), 1)) / max(portfolio_loss, 1e-9),
        })
    patterns=pd.DataFrame(patterns)
    if not patterns.empty:
        patterns = patterns.sort_values("Loss vs portfolio", ascending=False)
        patterns_display=patterns.copy()
        patterns_display["EAD"]=patterns_display["EAD"].map(format_money)
        patterns_display["Mean PD"]=patterns_display["Mean PD"].map(pct)
        patterns_display["ECL / EAD"]=patterns_display["ECL / EAD"].map(pct)
        patterns_display["PD vs portfolio"]=patterns_display["PD vs portfolio"].map(lambda v:f"{v:.2f}x")
        patterns_display["Loss vs portfolio"]=patterns_display["Loss vs portfolio"].map(lambda v:f"{v:.2f}x")
        st.dataframe(patterns_display, hide_index=True, width="stretch")

    st.markdown("#### Portfolio review actions")
    actions=[]
    high_ind = industry[(industry["Mean_PD"] >= portfolio_pd * 1.25) & (industry["Borrowers"] >= min_group)]
    for _, row in high_ind.iterrows():
        actions.append(f"Review {row['industry']} concentration: mean PD {pct(row['Mean_PD'])} versus portfolio {pct(portfolio_pd)}, across {int(row['Borrowers'])} borrowers and {format_money(row['EAD'])} EAD.")
    det = df[(df["risk_direction"]=="Deteriorating") & (df["credit_utilization"]>=.80)]
    if len(det) >= min_group:
        actions.append(f"Prioritize {len(det):,} deteriorating borrowers with utilization at or above 80%, representing {format_money(det['ead'].sum())} EAD.")
    s2u = df[df["stage"].isin(["Stage 2","Stage 3"]) & (df["recognized_collateral_coverage"]<=.01)]
    if len(s2u):
        actions.append(f"Review collateral/recovery strategy for {len(s2u):,} unsecured Stage 2/3 borrowers representing {format_money(s2u['ead'].sum())} EAD.")
    if not actions:
        actions.append("No broad portfolio trigger exceeds the current review thresholds; continue routine monitoring and case-level review.")
    for action in actions:
        st.write("• " + action)
    st.caption("Recommendations are transparent screening prompts based on broad monitoring thresholds and portfolio-relative comparisons; they do not approve, decline, stage or override a borrower.")

    stage_view=df.groupby("stage").agg(customers=("customer_id","count"),EAD=("ead","sum"),ECL=("ecl","sum")).reset_index()
    stage_view["EAD"]=stage_view["EAD"].map(format_money)
    stage_view["ECL"]=stage_view["ECL"].map(format_money)
    st.markdown("#### Stage distribution")
    st.dataframe(stage_view,hide_index=True,width="stretch")

    st.markdown("#### Highest-priority cases")
    priority=df.copy()
    priority["_priority"]=priority["ecl"].rank(pct=True)+priority["predicted_pd"].rank(pct=True)
    if "risk_direction" in priority.columns:
        priority["_priority"]+=priority["risk_direction"].eq("Deteriorating").astype(int)
    case_cols=[x for x in ["customer_id","industry","predicted_pd","risk_rating","rating_status","credit_score","risk_band","risk_direction","stage","days_past_due","ead","ecl"] if x in priority.columns]
    cases=priority.nlargest(12,"_priority")[case_cols].copy()
    if "predicted_pd" in cases: cases["predicted_pd"]=cases["predicted_pd"].map(pct)
    for money_col in ["ead","ecl"]:
        if money_col in cases: cases[money_col]=cases[money_col].map(format_money)
    st.dataframe(cases,hide_index=True,width="stretch")

with tabs[1]:
    st.subheader("Borrower Credit File")
    st.caption("One place to understand model risk, behaviour, exposure, staging and expected loss.")
    st.markdown("#### Find customer")
    search_mode = st.radio("Filter by", ["Customer number", "Risk rating", "Industry"], horizontal=True)
    customer_ids = df.customer_id.astype(str)
    filtered_customers = df.copy()

    if search_mode == "Customer number":
        customer_search = st.text_input("Customer number", placeholder="e.g. SME11286")
        if customer_search:
            filtered_customers = df[customer_ids.str.contains(customer_search.strip(), case=False, na=False, regex=False)]
    elif search_mode == "Risk rating":
        selected_rating = st.selectbox("Risk rating", sorted(df["risk_rating"].dropna().astype(int).unique().tolist()))
        filtered_customers = df[df["risk_rating"].astype(int).eq(selected_rating)]
    else:
        selected_industry = st.selectbox("Industry", sorted(df["industry"].dropna().astype(str).unique().tolist()))
        filtered_customers = df[df["industry"].astype(str).eq(selected_industry)]

    if filtered_customers.empty:
        st.warning("No customers match the selected filter. Showing the full portfolio instead.")
        filtered_customers = df

    cid = st.selectbox("Customer", filtered_customers.customer_id.astype(str).tolist())
    x = df[df.customer_id.astype(str).eq(cid)].iloc[0]
    a,b,c,d = st.columns(4)
    a.metric("PD", pct(x.predicted_pd))
    b.metric("Risk Rating", f"{int(x.risk_rating)}/10")
    c.metric("Rating status", str(x.rating_status))
    d.metric("Credit Score", f"{x.credit_score:.0f}")
    e,f,g,h = st.columns(4)
    e.metric("Risk band", str(x.risk_band))
    f.metric("Stage", str(x.stage))
    g.metric("LGD", pct(x.lgd))
    h.metric("ECL", format_money(x.ecl))
    st.markdown("#### Decision summary")
    ews=str(x["risk_direction"]) if "risk_direction" in df.columns else "—"
    st.write(f"**{x.risk_band}** model risk · **{ews}** EWS · **{x.stage}** accounting classification. "
             f"Internal Risk Rating is **{int(x.risk_rating)}/10 ({x.rating_status})**. "
             f"Exposure is **{format_money(x.ead)}** with LGD of **{pct(x.lgd)}** and expected loss of **{format_money(x.ecl)}**.")
    st.subheader("Exposure & recovery")
    recovery_rows = [
        ("Loan EAD", format_money(x.loan_ead)), ("OVD EAD", format_money(x.ovd_ead)),
        ("Trade EAD", format_money(x.trade_ead)), ("Total EAD", format_money(x.ead)),
        ("Collateral", format_money(x.collateral_value)), ("LGD", pct(x.lgd)),
    ]
    for field, label in [("recognized_collateral", "Recognized collateral"), ("unsecured_ead", "Unsecured EAD")]:
        if field in df.columns:
            recovery_rows.insert(-1, (label, format_money(x[field])))
    st.dataframe(pd.DataFrame(recovery_rows, columns=["Metric","Value"]), hide_index=True, width="stretch")
    st.subheader("Credit interpretation")
    adverse=[]
    if "leverage_ratio" in df.columns and x.leverage_ratio >= 3: adverse.append(f"leverage {x.leverage_ratio:.1f}x")
    if "credit_utilization" in df.columns and x.credit_utilization >= .8: adverse.append(f"utilization {x.credit_utilization:.1%}")
    if "delinquencies_12m" in df.columns and x.delinquencies_12m > 0: adverse.append(f"{int(x.delinquencies_12m)} delinquency event(s)")
    if "days_past_due" in df.columns and x.days_past_due > 0: adverse.append(f"{int(x.days_past_due)} DPD")
    if adverse: st.warning("Key adverse indicators: " + ", ".join(adverse) + ".")
    else: st.success("No significant adverse indicators.")
    if "forward_looking_pd_12m" in df.columns:
        st.write(f"Model PD **{pct(x.predicted_pd)}** → macro-adjusted 12M PD **{pct(x.forward_looking_pd_12m)}**. Accounting stage remains a separate decision dimension.")
    st.subheader("Qualitative underwriting")
    qcols=[c for c in [
        "management_quality","governance_quality","financial_reporting_quality",
        "market_position","sponsor_support","customer_concentration",
        "supplier_concentration","key_person_dependency","audit_quality"
    ] if c in df.columns]
    if qcols:
        st.dataframe(pd.DataFrame({"Field":qcols,"Value":[str(x[c]) for c in qcols]}), hide_index=True, width="stretch")

    st.subheader("Risk signals")
    cols=[c for c in ["days_past_due","credit_utilization","delinquencies_12m","previous_defaults","consecutive_ews_months","risk_direction","current_credit_impaired","write_off_flag"] if c in df.columns]
    st.dataframe(pd.DataFrame({"Field":cols,"Value":[str(x[c]) for c in cols]}), hide_index=True)

    if FACILITY_ECL.exists():
        fac = pd.read_csv(FACILITY_ECL)
        fac = fac[fac["customer_id"].astype(str).eq(str(cid))].copy()
        if not fac.empty:
            st.subheader("Facility LGD and ECL trace")
            show=[z for z in ["facility_id","product_type","ead_at_default","collateral_type","collateral_coverage","lien_rank","guarantee_coverage","predicted_lgd","remaining_months","stage","facility_pd_12m","facility_lifetime_pd","facility_ecl"] if z in fac.columns]
            st.dataframe(fac[show].style.format({
                'ead_at_default': '€{:,.2f}', 'facility_ecl': '€{:,.2f}',
                'predicted_lgd': '{:.2%}', 'facility_pd_12m': '{:.2%}', 'facility_lifetime_pd': '{:.2%}',
            }), hide_index=True, width="stretch")
            st.caption("Stage 1: 12-month forward-looking PD × LGD × EAD. Stage 2: facility lifetime PD × LGD × EAD. Stage 3: LGD × EAD. Borrower ECL is the sum of these facilities.")

with tabs[2]:
    st.subheader("Manual intervention")
    st.write("Model output is preserved. Overrides are separate governed decisions.")

    override_cid = st.selectbox(
        "Customer for intervention",
        df.customer_id.astype(str).tolist(),
        key="override_customer",
    )
    override_x = df[df.customer_id.astype(str).eq(override_cid)].iloc[0]

    if has_permission(role,"propose_override"):
        typ=st.selectbox("Override type",["PD","Risk band","Stage / SICR","Watchlist","Collateral / recovery"])
        proposed=st.text_input("Proposed value")
        reason=st.selectbox("Reason",["Qualitative risk","New information","Data correction","Credit committee judgement","Other"])
        rationale=st.text_area("Rationale")

        baseline_values = {
            "PD": f"{float(override_x.predicted_pd):.6f}",
            "Risk band": str(override_x.risk_band),
            "Stage / SICR": str(override_x.stage),
            "Watchlist": str(override_x.risk_direction),
            "Collateral / recovery": (
                f"{override_x.collateral_type}; recognized coverage="
                f"{float(override_x.recognized_collateral_coverage):.2%}"
            ),
        }
        model_value = baseline_values[typ]
        st.caption(f"Current value: {model_value}")

        if st.button("Submit for approval", disabled=not(proposed and rationale)):
            req = OverrideRequest(
                str(override_cid), typ, model_value, proposed,
                reason.upper().replace(" ","_"), rationale, user, role
            )
            try:
                req.validate()
                st.session_state["pending_override"] = req
                append_audit_event(AUDIT_LOG, {
                    "actor":user,"role":role,"action":"PROPOSE_OVERRIDE",
                    "customer_id":str(override_cid),"override_type":typ,
                    "model_value":model_value,"proposed_value":proposed,"reason":reason
                })
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
                    append_audit_event(AUDIT_LOG, {
                        "actor":user,"role":role,"action":"APPROVE_OVERRIDE",
                        "customer_id":req.customer_id,"override_type":req.override_type,
                        "model_value":req.model_value,"proposed_value":req.proposed_value
                    })
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
    st.dataframe(scenarios,width="stretch")
    if {"pit_pd_12m","forward_looking_pd_12m"}.issubset(df.columns):
        base=(df.pit_pd_12m*df.lgd*df.ead).sum()
        fwd=(df.forward_looking_pd_12m*df.lgd*df.ead).sum()
        m1,m2,m3=st.columns(3)
        m1.metric("PIT 12M diagnostic ECL",format_money(base))
        m2.metric("Forward-looking 12M ECL",format_money(fwd))
        m3.metric("Macro overlay impact",format_money(fwd-base))
    if has_permission(role,"manage_macro"):
        edited=st.data_editor(scenarios,width="stretch",num_rows="fixed")
        if st.button("Validate proposed scenarios"):
            try:
                validate_macro_scenarios(edited); st.success("Valid scenario set: weights sum to 100%.")
            except ValueError as e: st.error(str(e))
    else: st.info("Macro assumptions are read-only for this role.")

    st.markdown("#### Governance")
    st.info("Validated model coefficients are read-only. Policy, macro assumptions and human overrides are governed separately.")
    perms=["view_borrower","run_assessment","propose_override","approve_override","manage_policy","manage_macro","manage_users","view_audit"]
    st.dataframe(pd.DataFrame({"Permission":perms,"Allowed":[has_permission(role,p) for p in perms]}),hide_index=True)


if role == "Model Validation":
    with tabs[3]:
        st.subheader("Model Validation")
        st.caption("Independent validation view — hidden from Credit Analyst, Risk Manager, Auditor and Admin roles.")

        if not MODEL_VALIDATION.exists() or not CALIBRATION.exists():
            st.error("Run the credit-risk pipeline first to generate validation outputs.")
        else:
            validation = pd.read_csv(MODEL_VALIDATION)
            calibration = pd.read_csv(CALIBRATION)
            governed = validation.loc[validation["Model"].eq("Logistic Regression")].iloc[0]

            st.markdown("#### Governed PD performance")
            m1,m2,m3,m4,m5 = st.columns(5)
            m1.metric("ROC-AUC", f"{governed['ROC_AUC']:.4f}")
            m2.metric("Gini / AR", f"{governed['Gini']:.4f}")
            m3.metric("KS", f"{governed['KS']:.4f}")
            m4.metric("Brier", f"{governed['Brier']:.4f}")
            m5.metric("Log Loss", f"{governed['LogLoss']:.4f}")

            c1,c2,c3 = st.columns(3)
            c1.metric("Mean predicted PD", pct(governed["Mean_PD"]))
            c2.metric("Observed default rate", pct(governed["Observed_DR"]))
            c3.metric("Calibration-in-the-large", f"{governed['Calibration_in_the_large']*100:+.2f} pp")

            st.markdown("#### Calibration curve")
            st.caption("A credible PD model should not only rank borrowers; predicted probabilities should align reasonably with observed default frequencies out of sample.")
            chart = calibration.rename(columns={"mean_predicted_pd":"Predicted PD","observed_default_rate":"Observed default rate"})
            st.line_chart(chart.set_index("Predicted PD")["Observed default rate"], x_label="Mean predicted PD", y_label="Observed default rate")

            st.markdown("#### PD buckets — predicted vs observed")
            bucket_view = calibration.copy()
            rename = {
                "bucket":"PD bucket",
                "decile":"PD bucket",
                "n":"Borrowers",
                "count":"Borrowers",
                "mean_predicted_pd":"Mean predicted PD",
                "observed_default_rate":"Observed DR",
            }
            bucket_view = bucket_view.rename(columns={k:v for k,v in rename.items() if k in bucket_view.columns})
            for col in ["Mean predicted PD","Observed DR"]:
                if col in bucket_view.columns:
                    bucket_view[col] = bucket_view[col].map(pct)
            st.dataframe(bucket_view, hide_index=True, width="stretch")

            st.markdown("#### Validation interpretation")
            st.info("Discrimination (AUC/Gini/KS) evaluates rank ordering. Brier, Log Loss, calibration-in-the-large and bucket-level predicted-vs-observed default rates evaluate probability quality. Fixed classification thresholds are operational diagnostics and are not optimized on the holdout.")

            st.markdown("#### Facility workout LGD validation")
            if LGD_VALIDATION.exists() and LGD_CALIBRATION.exists():
                lgdv = pd.read_csv(LGD_VALIDATION)
                lgdc = pd.read_csv(LGD_CALIBRATION)
                st.dataframe(lgdv, width="stretch")
                governed_lgd = lgdv.loc[lgdv['Model'].eq('Gradient Boosting')].iloc[0]
                l1,l2,l3 = st.columns(3)
                l1.metric('LGD MAE', f"{100*governed_lgd['MAE']:.2f} pp")
                l2.metric('LGD RMSE', f"{100*governed_lgd['RMSE']:.2f} pp")
                l3.metric('LGD mean bias', f"{100*governed_lgd['Mean_Error_Bias']:+.2f} pp")
                st.caption("LGD validation is performed on a separate holdout of resolved synthetic defaulted facilities. Post-default recovery outcomes and workout timing are targets/audit fields, not model inputs.")
                lgd_chart = lgdc.rename(columns={"mean_predicted_lgd":"Predicted LGD","mean_actual_lgd":"Actual LGD"})
                if {"Predicted LGD","Actual LGD"}.issubset(lgd_chart.columns):
                    st.line_chart(lgd_chart.set_index("Predicted LGD")["Actual LGD"], x_label="Mean predicted LGD", y_label="Mean actual LGD")
                st.warning('High-loss underprediction remains a known limitation. Gradient Boosting remains the approved LGD model. Bias is predicted minus realized LGD; negative values indicate underprediction.')
                for title, filename in [
                    ('Realized-loss bands and segments', 'v5_lgd_realized_segments.csv'),
                    ('Challengers on the same facilities', 'lgd_fixed_cohort_tail_comparison.csv'),
                    ('Training and holdout support', 'v5_lgd_sample_support.csv'),
                    ('Train-to-holdout stability', 'lgd_train_holdout_stability.csv'),
                    ('Reapplied legacy proxy vs facility model', 'v5_lgd_legacy_holdout_comparison.csv'),
                    ('Portfolio ECL comparison with legacy LGD', 'ecl_methodology_bridge.csv'),
                    ('Release reconciliation checks', 'v5_release_checks.csv'),
                ]:
                    path = ROOT / 'outputs' / filename
                    with st.expander(title):
                        if path.exists():
                            st.dataframe(pd.read_csv(path), hide_index=True, width="stretch")
                        else:
                            st.info('Run the complete V5 build to generate this diagnostic.')
                st.caption('Realized-loss cohorts are retrospective and cannot identify facilities in advance. The legacy holdout benchmark reapplies the old proxy formula with a fixed synthetic residual seed; it is not an original historical forecast. Current-portfolio ECL differences are not accuracy metrics.')
            else:
                st.info("Run the LGD model pipeline to generate independent workout-LGD validation outputs.")
