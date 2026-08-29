from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from nexa.db.connection import engine
from nexa.db.models import Project

PROJECTS = [
    ("PRJ-001", "Warehouse Automation Phase 1", "أتمتة المستودعات المرحلة الأولى",
     "active", "operations", "high", "u-omar",
     date(2026, 1, 15), date(2026, 9, 30), 850000, 410000, 45),

    ("PRJ-002", "Fleet Tracking Upgrade", "تطوير نظام تتبع الأسطول",
     "active", "operations", "critical", "u-omar",
     date(2026, 2, 1), date(2026, 7, 31), 1200000, 980000, 72),

    ("PRJ-003", "HR Portal Redesign", "إعادة تصميم بوابة الموارد البشرية",
     "delayed", "hr", "medium", "u-fahad",
     date(2025, 11, 1), date(2026, 6, 30), 300000, 275000, 60),

    ("PRJ-004", "Customs Compliance System", "نظام الامتثال الجمركي",
     "on_hold", "legal", "high", "u-fahad",
     date(2026, 3, 1), date(2026, 12, 31), 600000, 90000, 15),

    ("PRJ-005", "Cold Chain Monitoring", "مراقبة سلسلة التبريد",
     "planning", "operations", "medium", "u-omar",
     date(2026, 9, 1), date(2027, 3, 31), 450000, 0, 0),

    ("PRJ-006", "Finance Reporting Automation", "أتمتة التقارير المالية",
     "completed", "finance", "medium", "u-fahad",
     date(2025, 6, 1), date(2026, 2, 28), 220000, 205000, 100),

    ("PRJ-007", "Driver Mobile App", "تطبيق السائقين",
     "active", "operations", "high", "u-omar",
     date(2026, 4, 1), date(2026, 11, 30), 700000, 190000, 28),

    ("PRJ-008", "Vendor Portal Integration", "تكامل بوابة الموردين",
     "delayed", "procurement", "low", "u-fahad",
     date(2025, 12, 1), date(2026, 8, 31), 380000, 340000, 55),
]


def seed_projects() -> None:
    with Session(engine) as session:
        session.query(Project).delete()

        for row in PROJECTS:
            (code, name_en, name_ar, status, dept, priority, owner,
             start, deadline, allocated, spent, progress) = row

            session.add(Project(
                id=code.lower().replace("-", "_"),
                code=code,
                name_en=name_en,
                name_ar=name_ar,
                description=f"{name_en} - {dept} department initiative.",
                status=status,
                department=dept,
                priority=priority,
                owner_id=owner,
                start_date=start,
                deadline=deadline,
                budget_allocated=Decimal(allocated),
                budget_spent=Decimal(spent),
                progress_percent=progress,
            ))

        session.commit()

    print(f"seeded {len(PROJECTS)} projects")


if __name__ == "__main__":
    seed_projects()