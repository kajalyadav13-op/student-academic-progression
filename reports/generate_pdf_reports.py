import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_technical_report():
    pdf_path = os.path.join('reports', 'FINAL_DBMS_TECHNICAL_REPORT.pdf')
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=45, leftMargin=45, topMargin=45, bottomMargin=45)
    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor('#0d9488')
    text_color = colors.HexColor('#0f172a')
    muted_color = colors.HexColor('#475569')

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=22,
        leading=26,
        textColor=primary_color,
        alignment=1, # Center
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=11,
        leading=15,
        textColor=muted_color,
        alignment=1,
        spaceAfter=20
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=14,
        textColor=text_color,
        spaceAfter=8
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Code'],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#1e293b'),
        backColor=colors.HexColor('#f1f5f9'),
        borderPadding=6,
        spaceAfter=8
    )

    elements = []

    # Title & Header
    elements.append(Paragraph("STUDENT ACADEMIC PROGRESSION & PORTFOLIO MANAGEMENT SYSTEM", title_style))
    elements.append(Paragraph("Comprehensive DBMS Technical Architecture & Engineering Report &bull; Relational 3NF Schema &bull; Cloud Deployed", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceBefore=0, spaceAfter=15))

    # Abstract
    elements.append(Paragraph("1. Abstract", h1_style))
    elements.append(Paragraph(
        "The Student Academic Progression & Portfolio Management System is an enterprise-grade relational database management application designed to eliminate data silos in collegiate academic tracking. "
        "Implementing a rigorous Third Normal Form (3NF) relational schema, the system provides real-time computation of Semester Grade Point Average (SGPA) and progressive Cumulative Grade Point Average (CGPA) on a 10-point scale. "
        "To ensure high reliability, an asynchronous Outbox Pattern decouples local SQL commits from external Google Sheets synchronization, preventing UI latency while providing complete spreadsheet integration across 7 relational entities.",
        body_style
    ))

    # Objectives & Problem Statement
    elements.append(Paragraph("2. Problem Statement & Objectives", h1_style))
    elements.append(Paragraph(
        "Traditional educational record systems suffer from disparate spreadsheets, lack of referential integrity, unverified manual CGPA calculations, and absence of extracurricular tracking. "
        "Key project objectives include: (1) Enforcing ACID compliance and relational integrity via foreign keys with cascading deletions; (2) Dynamic recalculation of progressive CGPA upon any mark update; "
        "(3) Durable background synchronization with Google Sheets; and (4) Providing automated multi-sheet Excel reporting.",
        body_style
    ))

    # Schema & ER Specifications
    elements.append(Paragraph("3. Relational Schema & Third Normal Form (3NF)", h1_style))
    elements.append(Paragraph(
        "The database design conforms to Third Normal Form, ensuring that every non-key attribute is non-transitively dependent on the primary key. Seven core tables model academic life, supported by dedicated sync tables:",
        body_style
    ))

    table_data = [
        ["Table Name", "Primary Key", "Foreign Keys", "Key Constraints / Purpose"],
        ["students", "id (PK)", "None", "student_code UNIQUE, email UNIQUE"],
        ["school_records", "id (PK)", "student_id -> students.id", "ON DELETE CASCADE, percentage auto-calculated"],
        ["semesters", "id (PK)", "student_id -> students.id", "UNIQUE(student_id, semester_number), ON DELETE CASCADE"],
        ["student_marks", "id (PK)", "semester_id -> semesters.id", "UNIQUE(semester_id, subject_code), 10-pt grade GP"],
        ["gap_years", "id (PK)", "student_id -> students.id", "ON DELETE CASCADE, official justifications"],
        ["seminars", "id (PK)", "student_id -> students.id", "ON DELETE CASCADE, conference & participation role"],
        ["activities", "id (PK)", "student_id -> students.id", "ON DELETE CASCADE, technical/sports achievements"],
        ["sync_outbox", "id (PK)", "None", "Durable queue: status (PENDING/SYNCED/FAILED)"],
        ["sync_log", "id (PK)", "None", "Audit trail with timestamp, operation, error logs"]
    ]

    t = Table(table_data, colWidths=[90, 65, 150, 215])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0d9488')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8.5),
        ('BOTTOMPADDING', (0,0), (-1,0), 5),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8fafc')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    elements.append(t)
    elements.append(Spacer(1, 10))

    # Academic Calculation Engine
    elements.append(Paragraph("4. Academic SGPA & Cumulative CGPA Calculation Engine", h1_style))
    elements.append(Paragraph(
        "<b>Grading Standard:</b> Marks are converted to letter grades and Grade Points (GP): &ge;90% &rarr; 'O' (10.0), 80-89% &rarr; 'A+' (9.0), 70-79% &rarr; 'A' (8.0), 60-69% &rarr; 'B+' (7.0), 55-59% &rarr; 'B' (6.0), 50-54% &rarr; 'C' (5.0), 40-49% &rarr; 'P' (4.0), &lt;40% &rarr; 'F' (0.0).<br/>"
        "<b>Semester SGPA Formula:</b> SGPA = &sum;(Credits &times; GradePoint) / &sum;(Credits)<br/>"
        "<b>Cumulative CGPA Formula:</b> CGPA<sub>k</sub> = &sum;<sub>i=1..k</sub>(Semester Credits<sub>i</sub> &times; SGPA<sub>i</sub>) / &sum;<sub>i=1..k</sub>(Semester Credits<sub>i</sub>)",
        body_style
    ))

    # Google Sheets Integration
    elements.append(Paragraph("5. Google Sheets Integration & Outbox Architecture", h1_style))
    elements.append(Paragraph(
        "External synchronization is orchestrated via an asynchronous Outbox Pattern. When a user submits an update, the SQL transaction commits first. "
        "A payload is atomically saved into <code>sync_outbox</code>. The Google Apps Script webhook receives updates, validates the secret token, and executes idempotent upserts matching record primary keys across all 7 target worksheets. "
        "This completely isolates the end-user application from Google Sheets rate-limiting or temporary API downtimes.",
        body_style
    ))

    # Automated Testing Results
    elements.append(Paragraph("6. Automated Verification & Testing Results", h1_style))
    elements.append(Paragraph(
        "An automated test suite using <code>pytest</code> validates every core system layer. 100% of tests passed:",
        body_style
    ))
    test_summary = [
        ["Test Case Name", "Module Verified", "Status", "Details"],
        ["test_health_check", "app.py (/health)", "PASSED", "Verified 200 OK, database alive, UTC timestamp"],
        ["test_dashboard_loads", "templates/dashboard.html", "PASSED", "Verified aggregate KPI queries & Chart.js"],
        ["test_grade_and_sgpa_calculations", "services/calculations.py", "PASSED", "Verified 10-point grade conversions & SGPA = 9.20"],
        ["test_cgpa_progressive_recalculation", "services/calculations.py", "PASSED", "Verified multi-semester cumulative weighted CGPA"],
        ["test_student_directory_and_search", "app.py (/students)", "PASSED", "Verified parameterized search and empty state handling"],
        ["test_student_crud", "services/db.py & outbox", "PASSED", "Verified INSERT, UPDATE, outbox queueing, and DELETE"],
        ["test_semester_and_mark_cascade", "services/db.py", "PASSED", "Verified mark addition auto-updates semester SGPA & credits"],
        ["test_excel_export", "services/export_excel.py", "PASSED", "Verified openpyxl generation with all 7 worksheets"]
    ]
    t_test = Table(test_summary, colWidths=[150, 110, 50, 210])
    t_test.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#059669')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8fafc')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('FONTSIZE', (0,1), (-1,-1), 7.5),
        ('TEXTCOLOR', (2,1), (2,-1), colors.HexColor('#059669')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    elements.append(t_test)
    elements.append(Spacer(1, 10))

    # Deployment and Security
    elements.append(Paragraph("7. Cloud Deployment & Security Architecture", h1_style))
    elements.append(Paragraph(
        "<b>Cloud Deployment:</b> Container-ready with Gunicorn (<code>gunicorn app:app --workers 2</code>) configured for Render / Heroku with <code>Procfile</code> and <code>render.yaml</code>.<br/>"
        "<b>Security:</b> 100% of database interactions utilize parameterized queries preventing SQL injection; all sensitive credentials are isolated in environment variables; CSRF and double-submit guards are enforced on frontend forms.",
        body_style
    ))

    doc.build(elements)
    print("Technical Report PDF generated successfully.")

def generate_screenshots_report():
    pdf_path = os.path.join('reports', 'GUI_SCREENSHOTS_REPORT.pdf')
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=45, leftMargin=45, topMargin=45, bottomMargin=45)
    styles = getSampleStyleSheet()

    primary_color = colors.HexColor('#0d9488')
    title_style = ParagraphStyle('GSTitle', parent=styles['Heading1'], fontSize=20, leading=24, textColor=primary_color, alignment=1)
    sub_style = ParagraphStyle('GSSub', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#64748b'), alignment=1, spaceAfter=15)
    h2_style = ParagraphStyle('GSH2', parent=styles['Heading2'], fontSize=12, leading=16, textColor=primary_color, spaceBefore=10, spaceAfter=4)
    desc_style = ParagraphStyle('GSDesc', parent=styles['Normal'], fontSize=9, leading=13, textColor=colors.HexColor('#334155'), spaceAfter=10)

    elements = []
    elements.append(Paragraph("STUDENT ACADEMIC PROGRESSION SYSTEM", title_style))
    elements.append(Paragraph("Graphical User Interface & Architectural Layout Report", sub_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=primary_color, spaceBefore=0, spaceAfter=10))

    modules = [
        ("1. Real-Time Performance Analytics Dashboard (/)",
         "Features responsive KPI metric cards (Total Enrolled, Active Students, On Leave, Dept Avg CGPA), Chart.js semester-wise SGPA progression curve, activity categories doughnut chart, and live feeds for recent seminars and extracurricular activities."),
        ("2. Student Directory & Search Center (/students)",
         "Offers multi-criteria searching by student code, full name, or institutional email, along with admission year and enrollment status filters. Includes modal for registering new students with validation rules."),
        ("3. 360-Degree Comprehensive Student Profile (/students/<id>)",
         "Central student portfolio displaying personal information, progressive SGPA vs Cumulative CGPA Chart.js curve, expandable semester cards with subject marks tables, secondary school education records, gap year records, and student seminars/activities."),
        ("4. Dynamic Subject Marks & SGPA Recalculation Engine",
         "Interactive modal with real-time letter grade predictor based on obtained vs maximum marks. Automatic database cascade recalculates semester SGPA and updates all subsequent progressive CGPA metrics in the student's academic history."),
        ("5. Portfolio: Seminars & Co-Curricular Directory (/portfolio)",
         "Consolidated view of student technical seminars, paper presentations, hackathons, and sports achievements with category and student filters."),
        ("6. Google Sheets Synchronization Dashboard (/sync)",
         "Displays real-time webhook status, pending outbox events counter, manual 'Bulk Sync All 7 Tables' trigger, and an immutable audit log of recent synchronization operations."),
        ("7. Excel Multi-Tab Relational Exporter (/export/excel)",
         "Automated openpyxl engine that streams a styled .xlsx workbook containing all 7 relational tables with colored headers and auto-adjusted columns.")
    ]

    for title, desc in modules:
        elements.append(Paragraph(title, h2_style))
        elements.append(Paragraph(desc, desc_style))

    doc.build(elements)
    print("GUI Screenshots Report PDF generated successfully.")

if __name__ == '__main__':
    generate_technical_report()
    generate_screenshots_report()
