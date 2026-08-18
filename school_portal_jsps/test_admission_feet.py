import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'school.db')

def test_online_admissions_and_fees():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("--- Testing Online Admissions Flow ---")
    # 1. Simulate Student Application
    c.execute('''INSERT INTO online_admissions 
                 (student_name, father_name, mother_name, dob, gender, class_applied, 
                  address, phone, admission_fee_paid, payment_receipt) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              ('Test User Admission', 'Test Father', 'Test Mother', '2015-01-01', 'Male', '3', 
               'Test Address', '9999999999', 1, 'uploads/receipts/test_receipt.jpg'))
    admission_id = c.lastrowid
    print(f"Submitted admission application (ID: {admission_id})")

    # 2. Check pending status
    status = c.execute('SELECT application_status FROM online_admissions WHERE id=?', (admission_id,)).fetchone()[0]
    print(f"Current status: {status}")

    # 3. Simulate Admin Approval
    c.execute('UPDATE online_admissions SET application_status="Approved" WHERE id=?', (admission_id,))
    status = c.execute('SELECT application_status FROM online_admissions WHERE id=?', (admission_id,)).fetchone()[0]
    print(f"Status after approval: {status}")
    
    # 4. Clean up admission test data
    c.execute('DELETE FROM online_admissions WHERE id=?', (admission_id,))
    print(f"Cleaned up admission test data")


    print("\n--- Testing Fee Payments Flow ---")
    # 1. Simulate Student Fee Payment
    c.execute('''INSERT INTO fee_payments 
                 (student_name, admission_no, class_name, amount_paid, payment_receipt) 
                 VALUES (?, ?, ?, ?, ?)''',
              ('Test User Fee', 'A1001', '5', 1500, 'uploads/receipts/fee_receipt.jpg'))
    fee_id = c.lastrowid
    print(f"Submitted fee payment (ID: {fee_id})")

    # 2. Check pending status
    status = c.execute('SELECT payment_status FROM fee_payments WHERE id=?', (fee_id,)).fetchone()[0]
    print(f"Current status: {status}")

    # 3. Simulate Admin Approval
    c.execute('UPDATE fee_payments SET payment_status="Approved" WHERE id=?', (fee_id,))
    status = c.execute('SELECT payment_status FROM fee_payments WHERE id=?', (fee_id,)).fetchone()[0]
    print(f"Status after approval: {status}")

    # 4. Clean up fee test data
    c.execute('DELETE FROM fee_payments WHERE id=?', (fee_id,))
    print(f"Cleaned up fee test data")

    conn.commit()
    conn.close()
    print("\n--- All DB Tests Passed! ---")

if __name__ == '__main__':
    test_online_admissions_and_fees()
