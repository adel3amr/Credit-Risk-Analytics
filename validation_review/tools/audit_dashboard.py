"""AppTest reconciliation against a clean frozen V5 snapshot and its CSVs."""
from pathlib import Path
import json
import sys
import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT=Path(sys.argv[1]).resolve()
OUT=Path(__file__).resolve().parents[1]/'evidence'
b=pd.read_csv(ROOT/'outputs/borrower_audit_trace.csv')
f=pd.read_csv(ROOT/'outputs/facility_ecl_predictions.csv')
pdval=pd.read_csv(ROOT/'outputs/model_validation.csv').set_index('Model').loc['Logistic Regression']
lgdval=pd.read_csv(ROOT/'outputs/lgd_model_validation.csv').set_index('Model').loc['Gradient Boosting']
app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=60)
def get(elements,label):return next(x for x in elements if x.label==label)
assert not app.exception
checks={}
def check(label,ok):checks[label]=bool(ok);assert ok,label
metric=lambda label:get(app.metric,label).value
check('hero borrower count',metric('Borrowers')==f'{len(b):,}')
check('hero mean PD',metric('Mean PD')==f'{b.predicted_pd.mean():.2%}')
check('hero EAD',metric('Total EAD')==f'€{b.ead.sum()/1e9:.2f}bn')
check('hero ECL',metric('Total ECL')==f'€{b.ecl.sum()/1e6:.2f}m')
for role in ['analyst.demo','risk.manager.demo','validator.demo','auditor.demo','admin.demo']:
    get(app.selectbox,'Demo identity').select(role).run(timeout=60)
    check('role '+role+' no error',not app.exception)
    labels=[x.label for x in app.tabs]
    check('role '+role+' required tabs',all(t in labels for t in
          ['Portfolio Cockpit','Borrower Credit File','Risk Management']))
    check('role '+role+' validation tab scope',('Model Validation' in labels)==(role=='validator.demo'))
    if role=='validator.demo':
        check('validator AUC',metric('ROC-AUC')==f'{pdval.ROC_AUC:.4f}')
        check('validator LGD bias',metric('LGD mean bias')==f"{lgdval.Mean_Error_Bias*100:+.2f} pp")
get(app.radio,'Filter by').set_value('Customer number').run(timeout=60)
cid=get(app.selectbox,'Customer').options[0]
get(app.selectbox,'Customer').select(cid).run(timeout=60)
facility_tables=[t.value for t in app.dataframe if 'facility_id' in t.value.columns]
check('facility table present',bool(facility_tables))
shown=facility_tables[0]
expected=f.loc[f.customer_id.eq(cid)]
check('facility table exact IDs',set(shown.facility_id)==set(expected.facility_id))
check('facility table ECL',abs(shown.facility_ecl.sum()-expected.facility_ecl.sum())<.005)
check('borrower ECL equals shown facilities',abs(expected.facility_ecl.sum()-b.set_index('customer_id').loc[cid,'ecl'])<.02)
output=dict(checks=checks,role_views=5,borrower_id=cid,facilities_rendered=len(shown),
            borrower_ecl=float(expected.facility_ecl.sum()))
(OUT/'dashboard_reconciliation.json').write_text(json.dumps(output,indent=2)+'\n')
print(f'{sum(checks.values())}/{len(checks)} dashboard checks passed; borrower {cid}')
