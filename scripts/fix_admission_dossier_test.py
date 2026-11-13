from pathlib import Path

test_path = Path("backend/tests/test_admission_dossier_demo.py")
code = test_path.read_text(encoding="utf-8")

old_s1 = '''    # 6. Collect Application Fee -> Triggers Immediate Auto-Enrolment
    r_pay1 = client.post(
        f"/admin/admission/applications/{aarav_id}/payments",
        json={
            "purpose": "application_fee",
            "amount": "500.00",
            "method": "cash",
            "reference": "REC-CASH-0101",
        },
        headers=admin,
    )
    assert r_pay1.status_code == 201, r_pay1.text
    pay_data1 = r_pay1.json()
    assert pay_data1["student"] is not None
    aarav_adm_no = pay_data1["student"]["admission_no"]
    aarav_student_id = pay_data1["student"]["id"]
    assert aarav_adm_no is not None and len(aarav_adm_no) > 0'''

new_s1 = '''    # 6. Collect Application Fee (advances to submitted) & Admission Fee (triggers conversion)
    r_pay1 = client.post(
        f"/admin/admission/applications/{aarav_id}/payments",
        json={
            "purpose": "application_fee",
            "amount": "500.00",
            "method": "cash",
            "reference": "REC-CASH-0101",
        },
        headers=admin,
    )
    assert r_pay1.status_code == 201, r_pay1.text

    client.post(f"/admin/admission/applications/{aarav_id}/status", json={"status": "decision_pending"}, headers=admin)
    client.post(f"/admin/admission/applications/{aarav_id}/decision", json={"decision": "admitted", "reason": "Evaluation passed"}, headers=admin)
    client.post(f"/admin/admission/applications/{aarav_id}/offer", json={"expires_on": "2026-12-31", "offer_amount": "25000"}, headers=admin)
    client.post(f"/admin/admission/applications/{aarav_id}/offer/response", json={"accepted": True}, headers=admin)

    r_adm1 = client.post(
        f"/admin/admission/applications/{aarav_id}/payments",
        json={
            "purpose": "admission_fee",
            "amount": "25000.00",
            "method": "cash",
            "reference": "REC-ADMFEE-0101",
        },
        headers=admin,
    )
    assert r_adm1.status_code == 201, r_adm1.text
    pay_data1 = r_adm1.json()
    assert pay_data1["student"] is not None
    aarav_adm_no = pay_data1["student"]["admission_no"]
    aarav_student_id = pay_data1["student"]["id"]
    assert aarav_adm_no is not None and len(aarav_adm_no) > 0'''

old_s2 = '''    # 7. Collect Application Fee & Auto-Enroll into Class 6
    r_pay2 = client.post(
        f"/admin/admission/applications/{ananya_id}/payments",
        json={
            "purpose": "application_fee",
            "amount": "500.00",
            "method": "upi",
            "reference": "UPI-HDFC-998822",
        },
        headers=admin,
    )
    assert r_pay2.status_code == 201, r_pay2.text
    pay_data2 = r_pay2.json()
    assert pay_data2["student"] is not None
    ananya_adm_no = pay_data2["student"]["admission_no"]
    ananya_student_id = pay_data2["student"]["id"]
    assert ananya_adm_no is not None and len(ananya_adm_no) > 0'''

new_s2 = '''    # 7. Collect Application Fee & Admission Fee to Auto-Enroll into Class 6
    r_pay2 = client.post(
        f"/admin/admission/applications/{ananya_id}/payments",
        json={
            "purpose": "application_fee",
            "amount": "500.00",
            "method": "upi",
            "reference": "UPI-HDFC-998822",
        },
        headers=admin,
    )
    assert r_pay2.status_code == 201, r_pay2.text

    client.post(f"/admin/admission/applications/{ananya_id}/status", json={"status": "decision_pending"}, headers=admin)
    client.post(f"/admin/admission/applications/{ananya_id}/decision", json={"decision": "admitted", "reason": "Sibling merit passed"}, headers=admin)
    client.post(f"/admin/admission/applications/{ananya_id}/offer", json={"expires_on": "2026-12-31", "offer_amount": "25000"}, headers=admin)
    client.post(f"/admin/admission/applications/{ananya_id}/offer/response", json={"accepted": True}, headers=admin)

    r_adm2 = client.post(
        f"/admin/admission/applications/{ananya_id}/payments",
        json={
            "purpose": "admission_fee",
            "amount": "25000.00",
            "method": "upi",
            "reference": "REC-ADMFEE-0102",
        },
        headers=admin,
    )
    assert r_adm2.status_code == 201, r_adm2.text
    pay_data2 = r_adm2.json()
    assert pay_data2["student"] is not None
    ananya_adm_no = pay_data2["student"]["admission_no"]
    ananya_student_id = pay_data2["student"]["id"]
    assert ananya_adm_no is not None and len(ananya_adm_no) > 0'''

assert old_s1 in code, "old_s1 not found"
assert old_s2 in code, "old_s2 not found"
code = code.replace(old_s1, new_s1, 1).replace(old_s2, new_s2, 1)
test_path.write_text(code, encoding="utf-8")
print("Updated test_admission_dossier_demo.py successfully")
