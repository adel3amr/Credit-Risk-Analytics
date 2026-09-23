"""Exercise all role views and borrower filter paths after a complete build."""
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def widget(elements, label):
    return next(element for element in elements if element.label == label)


if __name__ == '__main__':
    app = AppTest.from_file(str(ROOT / 'app.py')).run(timeout=60)
    assert not app.exception, app.exception
    for role in ['analyst.demo', 'risk.manager.demo', 'validator.demo', 'auditor.demo', 'admin.demo']:
        widget(app.selectbox, 'Demo identity').select(role).run(timeout=60)
        assert not app.exception, (role, app.exception)
        if role == 'validator.demo':
            assert any(t.label == 'Model Validation' for t in app.tabs)
            assert any(m.label == 'LGD mean bias' for m in app.metric)
    for mode in ['Risk rating', 'Industry', 'Customer number']:
        widget(app.radio, 'Filter by').set_value(mode).run(timeout=60)
        assert not app.exception, app.exception
    # Invalid regular-expression characters must be handled as literal input.
    widget(app.text_input, 'Customer number').set_value('[').run(timeout=60)
    assert not app.exception, app.exception
    widget(app.text_input, 'Customer number').set_value('').run(timeout=60)
    customers = widget(app.selectbox, 'Customer')
    customers.select(customers.options[-1]).run(timeout=60)
    assert not app.exception, app.exception
    print('Dashboard: all 5 role views, 3 filter modes, literal search and borrower drill-down passed')
