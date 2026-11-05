# FairMind AWS account and database study

**Date:** 4 Nov 2026
**Inputs:** live AWS CLI and Neon API reads, plus code under `apps/` and `deploy/lightsail/` on `main`. Every number below was read today unless it is marked "verify".

---

## 1. Summary

1. **Create a separate AWS account for FairMind.** Everything currently runs through an Olai IAM user, and no FairMind resources exist on AWS yet, so nothing needs migrating. The user has to create the account; Claude cannot sign up for accounts or create login credentials.
2. **Keep the database on Neon for now, but move production off the free plan this week.** The real production risk is the free plan, not Neon itself. FairMind uses almost nothing Neon-specific, so moving to AWS later is a one-hour job, not a rewrite.
3. **Move the database to AWS only when a concrete trigger fires** (section 5): for example, a customer that requires data stored in India, or a security review that demands a single cloud provider.

---

## 2. AWS account today

| What was checked | Result |
|---|---|
| Identity in use | An IAM user belonging to Olai, in an AWS account shared with Olai |
| AWS Organizations | None: the account is standalone, not part of an organisation |
| FairMind resources | None. The `deploy/lightsail` runbook (app on Lightsail us-east-1, 2 GB, $12) has not been run yet. |
| Other resources in the account | Olai's own EC2 instance and its networking and storage |

Hosting FairMind in Olai's account would mix two businesses' billing, access and ownership. A security buyer asking "who can reach your production data?" would get a messy answer. This is the cheapest moment to separate them, because nothing has been deployed yet.

### Steps (the user does these)

1. **Sign up** for a new AWS account using a company email alias that more than one person can receive, for example `aws@axonome.xyz`. Don't use a personal address.
2. **Secure the root user:** turn on MFA, then stop using root for daily work.
3. **Turn on IAM Identity Center**, create an admin user, then log in from the CLI with `aws configure sso --profile fairmind`. This uses short-lived credentials, with no long-lived access keys sitting on disk.
4. **Set cost alerts:** a $25 monthly budget alert in Billing, plus Cost Anomaly Detection.
5. **Apply for AWS Activate startup credits** under Axonome. This only works with an account the company owns.
6. **Point the AWS MCP server** at the `fairmind` profile (set `AWS_PROFILE` in its config). This is a setting on your machine, so you change it yourself.

After that, Claude can create the Ghost Micro instance, and later the app instance, in the new account.

**Same issue on Neon:** the Neon project is owned by a personal Gmail address (`subscription_type: free_v3`). Move it to an Axonome-owned Neon organisation at the same time.

---

## 3. What production uses on Neon today

| Item | Finding | Neon-only? |
|---|---|---|
| Project | `fairmind`, region aws-us-east-1, Postgres 18.6, autoscaling 0.25–2 CU | |
| Plan | **Free** (`free_v3`) | |
| Size | Database 17 MB; branch logical size about 41 MB; 99 tables | |
| Usage, 1–4 Nov | 60,056 s active time; 15,509 s of compute | |
| Branches | `production`, `demo` (used by the public demo stack), `production-backup-pre-assurance-2026-11-04` | Yes, branching |
| Neon Auth (Better Auth) | Provisioned, but **0 users, 0 sessions, 0 organisations**. The app signs people in with Authentik plus its own `users` table, and `NEON_AUTH_ENABLED` defaults to false. | Yes, but unused |
| `pg_session_jwt` extension | Installed. It's only needed for Neon Auth and the Data API. | Yes, but unused |
| Realtime | Enabled; the only allowed origin is `http://localhost:1111`. Used only by `apps/frontend/src/app/live-notes`. | Yes, experimental |
| Data API | Client in `apps/backend/services/neon_data_api.py`. Off unless `NEON_DATA_API_URL` is set. | Yes, optional |
| Logical replication | Enabled. Only Neon's internal physical slots exist; there are no publications. | No |

**Conclusion:** the application talks to plain Postgres through `DATABASE_URL`. The only Neon features production actually relies on are **branching** (the demo branch and pre-change backup branches) and **scale to zero**.

### Free-plan risks in production

- **Compute quota:** the free plan includes about 100 CU-hours per project per month. If you run out, the database stops until the next month. At 1–4 Nov usage it's about 30–40 CU-hours a month, but a busy demo or an always-on job would exhaust it.
- **Restore window:** only 6 hours of history (`history_retention_seconds: 21600`).
- **Storage cap:** about 0.5 GB per project on the free plan (verify; the API reports a 1 GB branch limit).
- **No SLA** and no support commitment.
- **Ownership:** the project sits on a personal account.

---

## 4. Options and monthly cost (us-east-1)

| Option | Monthly cost | What you get | What you give up |
|---|---|---|---|
| **A. Neon Launch** (pay as you go) | About $4–20: around $0.106 per CU-hour (verify; older sources say $0.14) times 30–180 CU-hours, plus $0.35 per GB-month of storage | Same setup, branching kept, longer restore window, no free-plan quota | Still a second vendor; no Mumbai region (Neon's nearest is Singapore) |
| **B. Lightsail managed Postgres**, Micro | **$15** (1 GB RAM, 40 GB disk, Postgres 18.6). HA version $30. | Private network to the Lightsail app box, one AWS bill, simple | No branching, so the demo needs a second database on the same instance. Fixed sizes. |
| **C. RDS Postgres** db.t4g.micro, Single-AZ | **$11.68 compute** ($0.016/h) plus about $2.30 for 20 GB gp3 storage (verify), about $14 total. A 1-year reservation with no upfront brings compute to $0.0116/h, about $8.50. Multi-AZ is roughly double. | Most production options: Multi-AZ, point-in-time restore up to 35 days, Mumbai available, Postgres 18.6 | Lightsail needs VPC peering to reach RDS privately; more configuration to manage |
| D. Postgres on the app box itself | $0 extra | — | You handle backups, failover and patching, all on a 2 GB box. **Not acceptable for production.** |

Notes:
- Both Lightsail and RDS offer Postgres 18.6, the same version Neon runs, so a migration needs no version change.
- New AWS accounts get starter credits, and Activate credits may cover B or C for the first year. Check the current terms for both.

---

## 5. When moving to AWS becomes the right call

Migrate (option C, or B if the app stays on Lightsail) when **any one** of these happens:

1. **India data residency:** a customer or contract requires data stored in India. Neon has no Mumbai region, while RDS and Lightsail both run in ap-south-1.
2. **Single cloud or private network required:** an enterprise security review demands it, and Neon's own certifications don't satisfy the reviewer.
3. **Uptime commitments:** you need Multi-AZ failover or an uptime SLA you can pass on to customers.
4. **Cost:** Neon compute regularly costs more than about $15 a month. At that point a fixed-price instance is cheaper.

Until then, Neon on a paid plan is cheaper, keeps branching (which the demo and your pre-change backups rely on) and needs no migration work.

---

## 6. How the migration would go, when it's needed

Expect about an hour of work and a few minutes of downtime at the current 17 MB.

1. **Clean up first** (worth doing even if you stay on Neon):
   - Drop the unused Neon Auth schema and the `pg_session_jwt` extension.
   - Decide whether live notes keeps Neon Realtime or switches to Postgres `LISTEN/NOTIFY` with server-sent events.
2. **Create the target database:** RDS or Lightsail, Postgres 18.6, private access only, automated backups on.
3. **Copy the data:** `pg_dump --no-owner --no-privileges --exclude-schema=neon_auth`, then `pg_restore` into the new database. Then run `apps/backend/scripts/verify_neon_migration.py`, or a row-count comparison per table.
4. **Replace the demo branch** with a separate `fairmind_demo` database on the same instance, and point `backend-demo.env` at it.
5. **Cut over:**
   - Put the app in maintenance mode.
   - Take a final dump and restore it.
   - Switch `DATABASE_URL` in `deploy/lightsail/backend.env`.
   - Run a smoke test.
   - Keep the Neon project read-only for 14 days as a fallback, then delete it.

---

## Sources

- **Live reads, 4 Nov 2026:**
  - AWS: `sts get-caller-identity`, `organizations describe-organization`, `lightsail get-bundles`, `get-relational-database-bundles`, `get-relational-database-blueprints`, `rds describe-db-engine-versions`, `pricing get-products` (AmazonRDS)
  - Neon: `list_projects`, `describe_project`, `list_branches`, `get_auth`, `get_realtime`, and read-only SQL
- **Code:** `deploy/lightsail/docker-compose.yml`, `deploy/lightsail/README.md`, `apps/backend/config/settings.py`, `apps/backend/core/middleware/auth.py`, `apps/backend/services/neon_data_api.py`, `apps/frontend/neon.ts`
- **Neon pricing** (secondary; verify on neon.com/pricing): [selfhost.dev](https://selfhost.dev/neon-pricing-cost-of-serverless-postgres/), [jetadmin.io](https://www.jetadmin.io/blog/neon-review/amp/), [costbench.com](https://www.costbench.com/software/database-as-service/neon/)
- **Neon regions:** [neon.com/docs/introduction/regions](https://neon.com/docs/introduction/regions), [community thread](https://community.neon.tech/t/hosting-in-other-aws-regions/81)
