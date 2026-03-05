# Database & Storage Setup (Neon-first)

## Database

Use a Neon PostgreSQL connection string in backend `.env`:

```bash
DATABASE_URL=postgresql://<user>:<password>@<neon-host>/<db>?sslmode=require
```

For local quick-start only:

```bash
DATABASE_URL=sqlite:///./fairmind.db
```

## Artifact Storage

Current default behavior:
- Model artifacts: local filesystem (`storage/models`)
- Dataset files: local filesystem (`uploads/datasets`)

Optional future step:
- Plug in a generic object storage adapter (S3/GCS/Azure Blob) behind service interfaces.

## Security Checklist

- Set strong `SECRET_KEY`.
- Restrict database credentials to least privilege.
- Enable SSL for all remote DB connections.
- Back up DB and local artifact directories.
