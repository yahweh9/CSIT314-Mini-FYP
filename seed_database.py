# seed_database.py
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

from entities.UserEntity import db, UserEntity
from entities.PINRequestEntity import PINRequestEntity
from entities.VolunteerServiceCategoryEntity import VolunteerServiceCategoryEntity as VCat
from entities.FeedbackEntity import FeedbackEntity

def _seed_categories_if_empty():
    """Seed dynamic categories derived from realistic activity types."""
    from entities.VolunteerServiceCategoryEntity import VolunteerServiceCategoryEntity as VCat

    if VCat.query.count() == 0:
        category_names = [
            "Food Donation Drive",
            "Community Clean-Up",
            "Health Awareness Event",
            "Elderly Home Visit",
            "Fundraising Campaign",
            "Recycling Workshop",
            "Beach Cleanup",
            "Tree Planting Activity",
            "Charity Walk",
            "Blood Donation Support"
        ]
        for name in category_names:
            db.session.add(VCat(
                name=name,
                description=f"Activities related to {name.lower()}",
                is_active=True
            ))
        db.session.commit()
        print(f"🌱 Seeded {len(category_names)} volunteer service categories.")


def seed_database():
    """Seed the database with initial test data"""

    # ---- Wipe tables we control (idempotent-ish for dev) ----
    # Order matters if you later add FKs; for now we clear requests then users.
    db.session.query(PINRequestEntity).delete()
    db.session.query(UserEntity).delete()

    # ---- Ensure categories exist BEFORE creating requests ----
    _seed_categories_if_empty()

    # Sample data generators
    companies = ["TechCorp Inc", "GreenEnergy Ltd", "FutureSolutions Co", "GlobalImpact Corp", "InnovateWorks"]
    departments = ["Engineering", "Marketing", "HR", "Finance", "Operations", "Sales", "IT"]
    addresses = [
        "123 Main St, Sydney", "456 Oak Ave, Melbourne", "789 Pine Rd, Brisbane",
        "321 Elm St, Perth", "654 Maple Dr, Adelaide", "987 Birch Ln, Canberra"
    ]

    # 1) Platform Manager
    pm = UserEntity(
        username='pm001',
        password=generate_password_hash('pm001'),
        role='pm',
        fullname='Platform Manager',
        email='platform.manager@csr-system.com',
        status='active',
        created_at=datetime.utcnow()
    )
    db.session.add(pm)

    # 2) Admins
    admins = [
        UserEntity(
            username='admin1',
            password=generate_password_hash('admin123'),
            role='admin',
            fullname='System Administrator',
            email='admin1@csr-system.com',
            status='active',
            created_at=datetime.utcnow() - timedelta(days=10)
        ),
        UserEntity(
            username='admin2',
            password=generate_password_hash('admin456'),
            role='admin',
            fullname='Support Administrator',
            email='admin2@csr-system.com',
            status='active',
            created_at=datetime.utcnow() - timedelta(days=5)
        )
    ]
    db.session.add_all(admins)

    # 3) CSR Reps
    csr_reps = []
    for i in range(1, 6):
        company = companies[i - 1]
        csr_rep = UserEntity(
            username=f'csr_rep{i}',
            password=generate_password_hash(f'csrrep{i}'),
            role='csrrep',
            fullname=f'CSR Representative {i}',
            email=f'csr{i}@{company.lower().replace(" ", "")}.com',
            company=company,
            status='active',
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
        )
        csr_reps.append(csr_rep)
        db.session.add(csr_rep)

    # 4) Corporate Volunteers
    corporate_volunteers = []
    first_names = ["John", "Jane", "Mike", "Sarah", "David", "Lisa", "Robert", "Emily", "Michael", "Jessica"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    for i in range(1, 51):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        company = random.choice(companies)
        department = random.choice(departments)
        cv = UserEntity(
            username=f'cv_{first_name.lower()}{i}',
            password=generate_password_hash(f'cvpassword{i}'),
            role='cv',
            fullname=f'{first_name} {last_name}',
            email=f'{first_name.lower()}.{last_name.lower()}@{company.lower().replace(" ", "")}.com',
            company=company,
            department=department,
            status='active' if i % 5 != 0 else 'pending',
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 60))
        )
        corporate_volunteers.append(cv)
        db.session.add(cv)

    # 5) Persons in Need
    pin_users = []
    pin_first_names = ["James", "Mary", "William", "Patricia", "Richard", "Jennifer", "Thomas", "Linda", "Charles", "Elizabeth"]
    pin_last_names = ["Wilson", "Anderson", "Taylor", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia"]
    for i in range(1, 51):
        first_name = random.choice(pin_first_names)
        last_name = random.choice(pin_last_names)
        address = random.choice(addresses)
        pin = UserEntity(
            username=f'pin_{first_name.lower()}{i}',
            password=generate_password_hash(f'pinpassword{i}'),
            role='pin',
            fullname=f'{first_name} {last_name}',
            email=f'{first_name.lower()}.{last_name.lower()}{i}@email.com',
            address=address,
            phone=f'04{random.randint(10000000, 99999999)}',
            status='active' if i % 4 != 0 else 'pending',
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 90))
        )
        pin_users.append(pin)
        db.session.add(pin)

    # Commit users & categories so we have IDs for FKs
    db.session.commit()

    try:
        # 6) PIN Requests
        pin_requests = []
        titles = [
            "Food Donation Drive", "Community Clean-Up", "Health Awareness Event",
            "Elderly Home Visit", "Fundraising Campaign", "Recycling Workshop",
            "Beach Cleanup", "Tree Planting Activity", "Charity Walk", "Blood Donation Support"
        ]

        # Preload categories for assignment
        categories = VCat.query.order_by(VCat.id.asc()).all()
        category_ids = [c.id for c in categories] if categories else [None]

        # ---- Assigned requests ----
        print("🟢 Creating assigned requests...")
        for i in range(1, 501):
            csr_rep = random.choice(csr_reps)
            pin = random.choice(pin_users)
            assigned_cv_id = random.choice(corporate_volunteers).user_id

            # 30% in the past (not completed), else future or completed
            if random.random() < 0.3:
                start_date = datetime.utcnow() - timedelta(days=random.randint(3, 15))
                end_date = start_date + timedelta(days=random.randint(1, 3))
                status = random.choice(["pending", "active"])
            else:
                start_date = datetime.utcnow() + timedelta(days=random.randint(1, 10))
                end_date = start_date + timedelta(days=random.randint(1, 5))
                status = random.choice(["pending", "active", "completed"])

            title = f"{random.choice(titles)} #{i}"

            # completed_date only if completed, and always logical
            completed_date = None
            if status == "completed":
                now = datetime.utcnow()
                latest_possible = min(end_date, now)
                earliest_possible = min(start_date + timedelta(hours=1), latest_possible)
                if earliest_possible < latest_possible:
                    delta_seconds = int((latest_possible - earliest_possible).total_seconds())
                    completed_date = earliest_possible + timedelta(seconds=random.randint(0, max(delta_seconds, 0)))
                else:
                    completed_date = latest_possible

            req = PINRequestEntity(
                requested_by_id=pin.user_id,
                assigned_to_id=assigned_cv_id,
                assigned_by_id=csr_rep.user_id,
                title=title,
                start_date=start_date,
                end_date=end_date,
                completed_date=completed_date,
                location=pin.address,
                description=f"Provide assistance to {pin.fullname} at {pin.address}",
                status=status,
                service_type=random.choice([c.name for c in categories]),
                urgency=random.choice(["low", "medium", "high"]),
                skills_required=random.choice([
                    "Communication", "Physical labor", "Teaching", "Cooking", "Driving", "First aid"
                ]),
                view_count=random.randint(0, 50),
                shortlist_count=0,
                # Attach a category (PM can update later in dashboard)
                volunteer_service_category_id=random.choice(category_ids)
            )
            pin_requests.append(req)
            db.session.add(req)

        # ---- Add extra unassigned requests ----
        print("🟡 Creating unassigned requests...")
        for i in range(1, 11):  # 10 unassigned requests
            csr_rep = random.choice(csr_reps)
            pin = random.choice(pin_users)

            start_date = datetime.utcnow() + timedelta(days=random.randint(1, 10))
            end_date = start_date + timedelta(days=random.randint(1, 5))
            status = "pending" # unassigned ones shouldn't be completed

            title = f"{random.choice(titles)} #{i}"

            req = PINRequestEntity(
                requested_by_id=pin.user_id,
                assigned_to_id=None,          # leave unassigned
                assigned_by_id=csr_rep.user_id,
                title=title,
                start_date=start_date,
                end_date=end_date,
                completed_date=None,
                location=pin.address,
                description=f"Unassigned request to assist {pin.fullname} at {pin.address}",
                status=status,
                service_type=random.choice([c.name for c in categories]),
                urgency=random.choice(["low", "medium", "high"]),
                skills_required=random.choice([
                    "Communication", "Physical labor", "Teaching", "Cooking", "Driving", "First aid"
                ]),
                view_count=0,
                shortlist_count=0,
                volunteer_service_category_id=random.choice(category_ids)
            )

            db.session.add(req)

        # ---- Add feedback for some completed requests ----
        print("⭐ Creating feedback for some completed requests...")
        completed_requests = [r for r in pin_requests if r.status == "completed"]

        # randomly pick around 30% of completed ones to have feedback
        sample_feedback_reqs = random.sample(
            completed_requests, 
            k=max(1, int(len(completed_requests) * 0.6))
        ) if completed_requests else []

        for req in sample_feedback_reqs:
            pin_id = req.requested_by_id
            rated_user_id = req.assigned_to_id
            rated_user_role = "cv"  # feedback from PIN about the Corporate Volunteer
            rating = random.randint(3, 5)
            comments = random.choice([
                "Very helpful and friendly.",
                "Good communication throughout.",
                "Task completed efficiently.",
                "Excellent support, would recommend.",
                "Satisfied with the assistance."
            ])

            feedback = FeedbackEntity(
                request_id=req.request_id,
                pin_id=pin_id,
                rated_user_id=rated_user_id,
                rated_user_role=rated_user_role,
                rating=rating,
                comments=comments
            )
            db.session.add(feedback)

        print(f"✅ Created {len(sample_feedback_reqs)} feedback entries.")

        db.session.commit()
        print("✅ Added unassigned requests successfully!")

        db.session.commit()

        print("✅ Database seeded successfully!")
        print_stats()

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error seeding database: {e}")

def print_stats():
    total_users = UserEntity.query.count()
    pm_count = UserEntity.query.filter_by(role='pm').count()
    admin_count = UserEntity.query.filter_by(role='admin').count()
    csrrep_count = UserEntity.query.filter_by(role='csrrep').count()
    cv_count = UserEntity.query.filter_by(role='cv').count()
    pin_count = UserEntity.query.filter_by(role='pin').count()
    pending_count = UserEntity.query.filter_by(status='pending').count()
    active_count = UserEntity.query.filter_by(status='active').count()
    req_count = PINRequestEntity.query.count()
    cat_count = VCat.query.count()

    print(f"\n📊 Database Statistics:")
    print(f"👥 Total Users: {total_users}")
    print(f"🏢 Platform Managers: {pm_count}")
    print(f"🔧 User Admins: {admin_count}")
    print(f"💼 CSR Representatives: {csrrep_count}")
    print(f"🤝 Corporate Volunteers: {cv_count}")
    print(f"🙋 Persons in Need: {pin_count}")
    print(f"📦 Requests: {req_count}")
    print(f"🏷️ Service Categories: {cat_count}")
    print(f"⏳ Pending Approvals: {pending_count}")
    print(f"✅ Active Users: {active_count}")

def get_sample_login_credentials():
    print(f"\n🔐 Sample Login Credentials:")
    pm = UserEntity.query.filter_by(role='pm').first()
    if pm:
        print(f"Platform Manager: username='{pm.username}', password='pm001'")
    admin = UserEntity.query.filter_by(role='admin').first()
    if admin:
        print(f"Admin: username='{admin.username}', password='admin123'")
    csr_rep = UserEntity.query.filter_by(role='csrrep').first()
    if csr_rep:
        print(f"CSR Rep: username='{csr_rep.username}', password='csrrep1'")
    cv = UserEntity.query.filter_by(role='cv', status='active').first()
    if cv:
        print(f"Corporate Volunteer: username='{cv.username}', password='cvpassword1'")
    pin = UserEntity.query.filter_by(role='pin', status='active').first()
    if pin:
        print(f"PIN: username='{pin.username}', password='pinpassword1'")

if __name__ == "__main__":
    from app import app
    with app.app_context():
        seed_database()
        get_sample_login_credentials()
