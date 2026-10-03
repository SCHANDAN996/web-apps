from app import app, db
from models import JobAlert
from datetime import datetime, timedelta

def populate_jobs():
    with app.app_context():
        # Clear existing jobs if any
        JobAlert.query.delete()
        
        jobs = [
            JobAlert(
                title="SSC CGL Recruitment 2026",
                organization="Staff Selection Commission",
                post_name="Inspector, Sub-Inspector, Assistant",
                vacancies="8,500+",
                eligibility="Graduation in any discipline",
                last_date="25 May 2026",
                application_url="https://ssc.nic.in",
                category="GOVT"
            ),
            JobAlert(
                title="SBI PO Recruitment 2026",
                organization="State Bank of India",
                post_name="Probationary Officer",
                vacancies="2,000",
                eligibility="Graduation in any discipline",
                last_date="30 June 2026",
                application_url="https://sbi.co.in/careers",
                category="BANKING"
            ),
            JobAlert(
                title="Software Engineer Campus Drive",
                organization="Tech Mahindra",
                post_name="Software Engineer",
                vacancies="500",
                eligibility="B.Tech/B.E (CS/IT)",
                last_date="15 May 2026",
                application_url="https://techmahindra.com/careers",
                category="PRIVATE"
            ),
            JobAlert(
                title="RRB NTPC Recruitment",
                organization="Railway Recruitment Board",
                post_name="Clerk, Station Master",
                vacancies="12,000",
                eligibility="12th Pass / Graduation",
                last_date="10 July 2026",
                application_url="https://indianrailways.gov.in",
                category="GOVT"
            ),
            JobAlert(
                title="IBPS Clerk Notification",
                organization="Institute of Banking Personnel Selection",
                post_name="Clerk",
                vacancies="5,000+",
                eligibility="Graduation in any discipline",
                last_date="20 August 2026",
                application_url="https://ibps.in",
                category="BANKING"
            )
        ]
        
        for job in jobs:
            db.session.add(job)
            
        db.session.commit()
        print("Successfully populated 5 mock job alerts.")

if __name__ == '__main__':
    populate_jobs()
