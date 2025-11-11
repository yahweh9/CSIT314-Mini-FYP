# seed_database.py
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random
from entities.UserEntity import db, UserEntity
from entities.PINRequestEntity import PINRequestEntity

def seed_database():
    """Seed the database with initial test data"""
    
    # Clear existing data
    db.session.query(UserEntity).delete()
    
    # Sample data generators
    companies = ["TechCorp Inc", "GreenEnergy Ltd", "FutureSolutions Co", "GlobalImpact Corp", "InnovateWorks"]
    departments = ["Engineering", "Marketing", "HR", "Finance", "Operations", "Sales", "IT"]
    addresses = [
        "123 Main St, Sydney", "456 Oak Ave, Melbourne", "789 Pine Rd, Brisbane",
        "321 Elm St, Perth", "654 Maple Dr, Adelaide", "987 Birch Ln, Canberra"
    ]
    
    # 1. Platform Manager (seeded once)
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
    
    # 2. User Admins (created by Platform Manager)
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
    for admin in admins:
        db.session.add(admin)
    
    # 3. CSR Representatives (created by Admins) - Limited accounts
    csr_reps = []
    for i in range(1, 6):  # 5 CSR Reps
        company = companies[i-1]
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
    
    # 4. Corporate Volunteers (self-registered, need approval)
    corporate_volunteers = []
    first_names = ["John", "Jane", "Mike", "Sarah", "David", "Lisa", "Robert", "Emily", "Michael", "Jessica"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    
    for i in range(1, 51):  # 50 Corporate Volunteers
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
            status='active' if i % 5 != 0 else 'pending',  # 80% approved, 20% pending
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 60))
        )
        corporate_volunteers.append(cv)
        db.session.add(cv)
    
    # 5. Persons in Need (self-registered, need approval)
    pin_users = []
    pin_first_names = ["James", "Mary", "William", "Patricia", "Richard", "Jennifer", "Thomas", "Linda", "Charles", "Elizabeth"]
    pin_last_names = ["Wilson", "Anderson", "Taylor", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia"]
    
    for i in range(1, 51):  # 50 PIN users
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
            phone=f'04{random.randint(10000000, 99999999)}',  # Australian mobile format
            status='active' if i % 4 != 0 else 'pending',  # 75% approved, 25% pending
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 90))
        )
        pin_users.append(pin)
        db.session.add(pin)

    # Commit all changes
    try:
        db.session.commit()

        # 6. PIN Requests (created by CSR Reps and assigned to CVs)
        

        pin_requests = []
        titles = [
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



        for i in range(1, 501):  # create 500 sample requests
            csr_rep = random.choice(csr_reps)
            pin = random.choice(pin_users)
            
            # Use the consistent mapping to assign CV to this PIN
            assigned_cv_id = random.choice(corporate_volunteers).user_id
            
            # randomly decide if this request is in the past or future
            if random.random() < 0.3:  # 30% chance to make it an expired one
                start_date = datetime.utcnow() - timedelta(days=random.randint(3, 15))
                end_date = start_date + timedelta(days=random.randint(1, 3))
                status = random.choice(["pending", "active"])  # expired ones are not completed
            else:
                start_date = datetime.utcnow() + timedelta(days=random.randint(1, 10))
                end_date = start_date + timedelta(days=random.randint(1, 5))
                status = random.choice(["pending", "active", "completed"])
            
            title = f"{random.choice(titles)} #{i}"

            # Generate completed_date ONLY if status is 'completed'
            completed_date = None
            if status == "completed":
                # Completion must be before today and after start_date
                latest_possible = min(end_date, datetime.utcnow())  # can't exceed now
                earliest_possible = start_date + timedelta(hours=1) # ensure logical sequence

                # If end_date is already in the future, make sure completed_date ≤ now
                if earliest_possible > latest_possible:
                    earliest_possible = latest_possible - timedelta(hours=1)

                # Randomly pick a date between earliest_possible and latest_possible
                delta_seconds = int((latest_possible - earliest_possible).total_seconds())
                completed_date = earliest_possible + timedelta(seconds=random.randint(0, delta_seconds))

            request = PINRequestEntity(
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
                service_type=random.choice(["cleanup", "elderly", "education", "food", "community", "environment", "health", "fundraising"]),
                urgency=random.choice(["low", "medium", "high"]),
                skills_required=random.choice(["Communication", "Physical labor", "Teaching", "Cooking", "Driving", "First aid"]),
                view_count=random.randint(0, 50),
                shortlist_count=random.randint(0, 10)
            )
            pin_requests.append(request)
            db.session.add(request)

        db.session.commit()

        print("✅ Database seeded successfully!")
        print_stats()
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error seeding database: {e}")

        
def print_stats():
    """Print statistics about the seeded data"""
    total_users = UserEntity.query.count()
    pm_count = UserEntity.query.filter_by(role='pm').count()
    admin_count = UserEntity.query.filter_by(role='admin').count()
    csrrep_count = UserEntity.query.filter_by(role='csrrep').count()
    cv_count = UserEntity.query.filter_by(role='cv').count()
    pin_count = UserEntity.query.filter_by(role='pin').count()
    pending_count = UserEntity.query.filter_by(status='pending').count()
    active_count = UserEntity.query.filter_by(status='active').count()
    
    print(f"\n📊 Database Statistics:")
    print(f"👥 Total Users: {total_users}")
    print(f"🏢 Platform Managers: {pm_count}")
    print(f"🔧 User Admins: {admin_count}")
    print(f"💼 CSR Representatives: {csrrep_count}")
    print(f"🤝 Corporate Volunteers: {cv_count}")
    print(f"🙋 Persons in Need: {pin_count}")
    print(f"⏳ Pending Approvals: {pending_count}")
    print(f"✅ Active Users: {active_count}")

def get_sample_login_credentials():
    """Get sample login credentials for testing"""
    print(f"\n🔐 Sample Login Credentials:")
    
    # Platform Manager
    pm = UserEntity.query.filter_by(role='pm').first()
    print(f"Platform Manager: username='{pm.username}', password='pm001'")
    
    # Admin
    admin = UserEntity.query.filter_by(role='admin').first()
    print(f"Admin: username='{admin.username}', password='admin123'")
    
    # CSR Rep
    csr_rep = UserEntity.query.filter_by(role='csrrep').first()
    print(f"CSR Rep: username='{csr_rep.username}', password='csrrep1'")
    
    # Corporate Volunteer
    cv = UserEntity.query.filter_by(role='cv', status='active').first()
    print(f"Corporate Volunteer: username='{cv.username}', password='cvpassword1'")
    
    # PIN
    pin = UserEntity.query.filter_by(role='pin', status='active').first()
    print(f"PIN: username='{pin.username}', password='pinpassword1'")

if __name__ == "__main__":
    # Import your app to get the database context
    from app import app
    
    with app.app_context():
        seed_database()
        get_sample_login_credentials()