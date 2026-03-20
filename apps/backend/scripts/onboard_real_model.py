#!/usr/bin/env python3
"""
Onboard an actual model artifact into FairMind Neon runtime.

Example:
  DATABASE_URL=... python scripts/onboard_real_model.py \
    --file apps/backend/uploads/models/pilot_credit_lr.pkl \
    --name "Axonome Credit Logistic v1" \
    --model-type classification \
    --version 1.0.0 \
    --owner-email adhi@axonome.xyz \
    --description "Real trained logistic baseline for pilot credit flow"
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from database.connection import db_manager


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Path to model artifact (.pkl/.onnx/.pt/...)")
    parser.add_argument("--name", required=True)
    parser.add_argument("--model-type", required=True)
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument("--description", default="Real model onboarded for pilot")
    parser.add_argument("--owner-email", default="adhi@axonome.xyz")
    args = parser.parse_args()

    src = Path(args.file).resolve()
    if not src.exists():
        raise SystemExit(f"Model file not found: {src}")

    model_id = f"real-{uuid.uuid4()}"
    ext = src.suffix or ".bin"
    storage_dir = Path(__file__).resolve().parent.parent / "uploads" / "models"
    storage_dir.mkdir(parents=True, exist_ok=True)
    dst = storage_dir / f"{model_id}{ext}"
    shutil.copy2(src, dst)

    checksum = sha256_file(dst)
    now = datetime.now(timezone.utc)

    with db_manager.get_session() as session:
        user = session.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": args.owner_email},
        ).fetchone()
        if not user:
            raise SystemExit(f"Owner user not found for email: {args.owner_email}")
        user_id = str(user[0])

        session.execute(
            text(
                """
                INSERT INTO models (id, name, description, model_type, version, file_path, file_size, status, tags, metadata, created_by, upload_date, updated_at)
                VALUES (:id, :name, :description, :model_type, :version, :file_path, :file_size, :status, CAST(:tags AS jsonb), CAST(:metadata AS jsonb), :created_by, :upload_date, :updated_at)
                """
            ),
            {
                "id": model_id,
                "name": args.name,
                "description": args.description,
                "model_type": args.model_type,
                "version": args.version,
                "file_path": f"/uploads/models/{dst.name}",
                "file_size": dst.stat().st_size,
                "status": "active",
                "tags": json.dumps(["real-model", "pilot", "onboarded"]),
                "metadata": json.dumps(
                    {
                        "artifact_sha256": checksum,
                        "artifact_original_name": src.name,
                        "artifact_extension": ext,
                        "onboarded_at": now.isoformat(),
                        "onboarded_via": "scripts/onboard_real_model.py",
                    }
                ),
                "created_by": user_id,
                "upload_date": now,
                "updated_at": now,
            },
        )

        session.execute(
            text(
                """
                INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details, created_at)
                VALUES (:user_id, :action, :resource_type, :resource_id, CAST(:details AS jsonb), :created_at)
                """
            ),
            {
                "user_id": user_id,
                "action": "real_model_onboarded",
                "resource_type": "models",
                "resource_id": model_id,
                "details": json.dumps(
                    {
                        "name": args.name,
                        "version": args.version,
                        "file_path": f"/uploads/models/{dst.name}",
                        "sha256": checksum,
                    }
                ),
                "created_at": now,
            },
        )
        session.commit()

    print(f"Model onboarded: {model_id}")
    print(f"Stored file: {dst}")
    print(f"SHA256: {checksum}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
