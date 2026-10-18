import os
import pytest
import io
import openpyxl
from app import app
from config import Config
from services import db, calculations, google_sheets, export_excel

@pytest.fixture
def client():
    # Use temporary SQLite DB for testing
    test_db = os.path.join(os.path.dirname(__file__), 'test_academic.db')
    Config.SQLITE_PATH = test_db
    Config.DB_TYPE = 'sqlite'
    app.config['TESTING'] = True
    
    # Initialize fresh DB
    if os.path.exists(test_db):
        os.remove(test_db)
    db.init_db(seed_if_empty=True)

    with app.test_client() as client:
        yield client

    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except Exception:
            pass

def test_health_check(client):
    res = client.get('/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'healthy'
    assert data['database'] == 'connected'

def test_dashboard_loads(client):
    res = client.get('/')
    assert res.status_code == 200
    assert b'Academic Performance Dashboard' in res.data
    assert b'Total Enrolled' in res.data

def test_grade_and_sgpa_calculations():
    # Test Grade Points
    g, gp = calculations.get_grade_and_point(95, 100)
    assert g == 'O' and gp == 10.0
    
    g, gp = calculations.get_grade_and_point(85, 100)
    assert g == 'A+' and gp == 9.0

    g, gp = calculations.get_grade_and_point(35, 100)
    assert g == 'F' and gp == 0.0

    # Test SGPA calculation
    marks = [
        {'credits': 4.0, 'obtained_marks': 92.0, 'max_marks': 100.0, 'grade': 'O'},   # 4 * 10 = 40
        {'credits': 4.0, 'obtained_marks': 82.0, 'max_marks': 100.0, 'grade': 'A+'},  # 4 * 9 = 36
        {'credits': 2.0, 'obtained_marks': 75.0, 'max_marks': 100.0, 'grade': 'A'}    # 2 * 8 = 16
    ]
    # Total credits = 10, total points = 92. SGPA = 92/10 = 9.20
    credits, sgpa = calculations.calculate_sgpa(marks)
    assert credits == 10.0
    assert sgpa == 9.20

def test_cgpa_progressive_recalculation():
    sems = [
        {'semester_number': 1, 'credits': 20.0, 'sgpa': 9.0}, # pts = 180, credits = 20 -> cgpa 9.0
        {'semester_number': 2, 'credits': 20.0, 'sgpa': 8.0}  # pts = 160, total pts = 340, total credits = 40 -> cgpa 8.5
    ]
    updated = calculations.recalculate_student_cgpa(sems)
    assert updated[0]['cgpa'] == 9.0
    assert updated[1]['cgpa'] == 8.5

def test_student_directory_and_search(client):
    # Check directory
    res = client.get('/students')
    assert res.status_code == 200
    assert b'Aarav Sharma' in res.data

    # Search existing student
    res_search = client.get('/students?search=Aarav')
    assert b'Aarav Sharma' in res_search.data

    # Search non-existing
    res_empty = client.get('/students?search=NonExistentPersonXYZ')
    assert b'No student records match' in res_empty.data

def test_student_crud(client):
    # Create new student
    post_data = {
        'student_code': 'TEST2026',
        'full_name': 'Test Student',
        'email': 'test.student@demo.edu',
        'admission_year': '2024',
        'current_status': 'Active'
    }
    res = client.post('/students/create', data=post_data, follow_redirects=True)
    assert res.status_code == 200
    assert b'Test Student' in res.data

    # Verify student exists in DB
    student = db.query_one("SELECT * FROM students WHERE student_code = %s", ('TEST2026',))
    assert student is not None
    assert student['full_name'] == 'Test Student'

    # Verify outbox event queued
    outbox = db.query_one("SELECT * FROM sync_outbox WHERE record_id = %s AND entity_name = 'Students'", (student['id'],))
    assert outbox is not None
    assert outbox['status'] == 'PENDING'

    # Edit student
    client.post(f"/students/{student['id']}/edit", data={
        'student_code': 'TEST2026',
        'full_name': 'Updated Test Student',
        'email': 'test.student@demo.edu',
        'admission_year': '2024',
        'current_status': 'On Leave'
    }, follow_redirects=True)

    updated_student = db.query_one("SELECT * FROM students WHERE id = %s", (student['id'],))
    assert updated_student['full_name'] == 'Updated Test Student'
    assert updated_student['current_status'] == 'On Leave'

    # Delete student
    client.post(f"/students/{student['id']}/delete", follow_redirects=True)
    deleted_check = db.query_one("SELECT * FROM students WHERE id = %s", (student['id'],))
    assert deleted_check is None

def test_semester_and_mark_cascade(client):
    student = db.query_one("SELECT id FROM students LIMIT 1")
    s_id = student['id']

    # Add a new semester
    client.post(f"/students/{s_id}/semesters/add", data={
        'semester_number': 8,
        'academic_year': '2025-2026'
    }, follow_redirects=True)

    sem = db.query_one("SELECT id FROM semesters WHERE student_id = %s AND semester_number = 8", (s_id,))
    assert sem is not None

    # Add mark to semester
    client.post(f"/semesters/{sem['id']}/marks/add", data={
        'subject_code': 'CS801',
        'subject_name': 'Advanced Cloud Architecture',
        'credits': 4.0,
        'max_marks': 100.0,
        'obtained_marks': 95.0
    }, follow_redirects=True)

    # Check that SGPA was calculated
    updated_sem = db.query_one("SELECT * FROM semesters WHERE id = %s", (sem['id'],))
    assert updated_sem['credits'] == 4.0
    assert updated_sem['sgpa'] == 10.00  # 95/100 -> 'O' = 10 GP

def test_excel_export(client):
    res = client.get('/export/excel')
    assert res.status_code == 200
    assert res.headers['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    # Load with openpyxl to verify valid workbook
    wb = openpyxl.load_workbook(io.BytesIO(res.data))
    sheet_names = wb.sheetnames
    assert 'Students' in sheet_names
    assert 'Semesters' in sheet_names
    assert 'StudentMarks' in sheet_names
    assert 'SchoolRecords' in sheet_names
    assert 'GapYears' in sheet_names
    assert 'Seminars' in sheet_names
    assert 'Activities' in sheet_names
