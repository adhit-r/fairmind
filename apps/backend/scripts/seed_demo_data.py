"""
Seed Demo Data Script
Seeds the database with specific demo data:
- Company: Axonome
- User: Adhi
- Synthetic Models and Reports
"""

import sys
import uuid
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from sqlalchemy import text

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import db_manager

def seed_demo_data():
    print("=" * 80)
    print("Seeding Demo Data (Axonome)")
    print("=" * 80)

    if not db_manager.test_connection():
        print("ERROR: Database connection failed!")
        return False

    with db_manager.get_session() as session:
        # 1. Create/Ensure User "Adhi"
        demo_user_id = str(uuid.uuid4())
        try:
            # Check if user table exists and insert
            user_data = {
                "id": demo_user_id,
                "email": "adhi@axonome.xyz",
                "full_name": "Adhi",
                "role": "admin",
                "hashed_password": "$2b$12$7TjiHtGXh1fo/DZ7J3.1oeIP8ZU.QB9mfb2gF7YnFmgQJ2bL7XHVS",
                "created_at": datetime.now(timezone.utc)
            }
            
            upsert_user_sql = text("""
                INSERT INTO users (id, email, full_name, role, hashed_password, created_at)
                VALUES (:id, :email, :full_name, :role, :hashed_password, :created_at)
                ON CONFLICT(email) DO UPDATE SET
                full_name = :full_name
            """)
            
            try:
                session.execute(upsert_user_sql, user_data)
                session.commit()
                print(f"✓ User 'Adhi' (Axonome) created/updated.")
            except Exception as e:
                # Handle table creation if needed (omitted for brevity as table exists)
                raise e

        except Exception as e:
            print(f"✗ Failed to seed user: {e}")
            session.rollback()

        # 2. Create Synthetic Models for Axonome
        models = [
            {
                "name": "Axonome Customer Insight",
                "type": "classification",
                "desc": "Predicts customer behavior and churn risks.",
                "tags": ["churn", "customer", "enterprise"],
                "bias_risk": "low"
            },
            {
                "name": "Axonome Credit Scoring Alpha",
                "type": "classification",
                "desc": "Next-gen credit scoring model for diverse markets.",
                "tags": ["finance", "credit", "innovative"],
                "bias_risk": "medium"
            },
            {
                "name": "Axonome Talent Scout",
                "type": "nlp",
                "desc": "AI-powered candidate screening and matching.",
                "tags": ["hr", "hiring", "nlp"],
                "bias_risk": "low"
            },
            {
                "name": "Axonome Vision Guard",
                "type": "cv",
                "desc": "Computer vision for safety monitoring.",
                "tags": ["vision", "safety", "monitoring"],
                "bias_risk": "medium"
            }
        ]

        for m in models:
            m_id = str(uuid.uuid4())
            try:
                model_data = {
                    "id": m_id,
                    "name": m["name"],
                    "description": m["desc"],
                    "model_type": m["type"],
                    "version": "1.0.0",
                    "status": "active",
                    "tags": json.dumps(m["tags"]),
                    "metadata": json.dumps({"organization": "Axonome", "risk_profile": m['bias_risk']}),
                    "created_by": demo_user_id,
                    "upload_date": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "file_path": f"/models/{m_id}.pkl",
                    "file_size": 1024 * 1024
                }
                
                # ... insert logic ...
                insert_model = text("""
                    INSERT INTO models (
                        id, name, description, model_type, version, status, tags, metadata, 
                        created_by, upload_date, updated_at, file_path, file_size
                    ) VALUES (
                        :id, :name, :description, :model_type, :version, :status, :tags, :metadata,
                        :created_by, :upload_date, :updated_at, :file_path, :file_size
                    )
                """)
                session.execute(insert_model, model_data)
                session.commit()
                print(f"✓ Model '{m['name']}' created.")
                
                 # Add a bias analysis for this model
                analysis_data = {
                    "id": str(uuid.uuid4()),
                    "model_id": m_id,
                    "analysis_type": "demographic_parity",
                    "status": "completed",
                    "results": json.dumps({"passed": m['bias_risk'] == 'low', "risk": m['bias_risk']}),
                    "metrics": json.dumps({"disparity": 0.05 if m['bias_risk'] == 'low' else 0.15}),
                    "created_by": demo_user_id,
                    "created_at": datetime.now(timezone.utc),
                    "completed_at": datetime.now(timezone.utc)
                }
                
                insert_analysis = text("""
                    INSERT INTO bias_analyses (
                        id, model_id, analysis_type, status, results, metrics, created_by, created_at, completed_at
                    ) VALUES (
                        :id, :model_id, :analysis_type, :status, :results, :metrics, :created_by, :created_at, :completed_at
                    )
                """)
                session.execute(insert_analysis, analysis_data)
                session.commit()

            except Exception as e:
                print(f"✗ Failed to create model {m['name']}: {e}")
                session.rollback()

    return True

if __name__ == "__main__":
    seed_demo_data()
