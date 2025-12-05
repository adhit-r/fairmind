import os
import sys
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
from supabase import create_client, Client

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Load env vars manually since we might not be running through main app
from dotenv import load_dotenv
load_dotenv()

async def seed_datasets():
    print("Initializing Supabase client...")
    url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        print("Error: Supabase credentials not found in environment variables.")
        print("Please ensure NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set in apps/backend/.env")
        return

    try:
        supabase: Client = create_client(url, key)
    except Exception as e:
        print(f"Failed to create Supabase client: {e}")
        return

    # 1. Generate Credit Risk Dataset
    print("Generating Credit Risk Dataset...")
    np.random.seed(42)
    n = 1000
    credit_df = pd.DataFrame({
        "age": np.random.randint(18, 80, n),
        "income": np.random.normal(50000, 15000, n),
        "gender": np.random.choice(['Male', 'Female'], n),
        "ethnicity": np.random.choice(['Group A', 'Group B', 'Group C'], n),
        "credit_score": np.random.randint(300, 850, n),
        "approved": np.random.randint(0, 2, n)
    })
    
    # 2. Generate Hiring Dataset
    print("Generating Hiring Dataset...")
    n = 500
    hiring_df = pd.DataFrame({
        "experience_years": np.random.randint(0, 20, n),
        "education_level": np.random.choice(['BS', 'MS', 'PhD'], n),
        "gender": np.random.choice(['Male', 'Female'], n),
        "hired": np.random.randint(0, 2, n)
    })

    datasets = [
        ("credit_risk.csv", credit_df, "Credit Risk Data", "Historical credit application data"),
        ("hiring.csv", hiring_df, "Hiring Decisions", "Resume screening data")
    ]

    # Try to create bucket if possible (usually requires SQL or dashboard, but client might have permissions)
    # We'll just try to upload
    
    for filename, df, name, description in datasets:
        print(f"Processing {name}...")
        
        # Convert to CSV
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        
        # Upload to Storage
        path = f"{filename}" # Root of bucket
        try:
            # Check if bucket exists by listing? No, just try upload
            # We assume bucket 'datasets' exists. If not, user needs to run SQL.
            res = supabase.storage.from_("datasets").upload(
                path=path,
                file=csv_content,
                file_options={"content-type": "text/csv", "upsert": "true"}
            )
            print(f"Uploaded {filename} to Storage.")
        except Exception as e:
            print(f"Failed to upload {filename} (Bucket 'datasets' might not exist): {e}")
            
            # Fallback: Save locally
            print(f"Fallback: Saving {filename} locally...")
            local_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'datasets')
            os.makedirs(local_dir, exist_ok=True)
            local_path = os.path.join(local_dir, filename)
            with open(local_path, "wb") as f:
                f.write(csv_content)
            print(f"Saved {filename} to {local_path}")
            path = str(local_path) # Use local path for metadata if needed, but DB insert might fail anyway
        
        # Insert Metadata into DB
        metadata = {
            "name": name,
            "description": description,
            "file_path": path, # Store relative path in bucket
            "file_type": "csv",
            "row_count": len(df),
            "column_count": len(df.columns),
            "file_size": len(csv_content),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "schema": {
                "columns": [{"name": c, "type": str(t)} for c, t in df.dtypes.items()]
            }
        }
        
        try:
            # Check if exists
            existing = supabase.table("datasets").select("id").eq("name", name).execute()
            if existing.data:
                # Update
                dataset_id = existing.data[0]['id']
                supabase.table("datasets").update(metadata).eq("id", dataset_id).execute()
                print(f"Updated metadata for {name}.")
            else:
                # Insert
                supabase.table("datasets").insert(metadata).execute()
                print(f"Inserted metadata for {name}.")
        except Exception as e:
            print(f"Failed to insert metadata for {name} (Table 'datasets' might not exist): {e}")
            print("Please run apps/backend/database/migrations/init_supabase.sql in Supabase SQL Editor.")

if __name__ == "__main__":
    asyncio.run(seed_datasets())
