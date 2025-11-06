# ⚡ FairMind Quick Start

**Get up and running in 2 minutes!**

## 🚀 Fastest Setup

```bash
# 1. Clone
git clone https://github.com/adhit-r/fairmind.git && cd fairmind

# 2. Backend (Terminal 1)
cd apps/backend && uv sync && uv run python -m uvicorn api.main:app --reload

# 3. Frontend (Terminal 2)
cd apps/frontend && bun install && bun run dev
```

**✅ Done!** Visit `http://localhost:3000`

## 📋 Requirements

- Python 3.9+ → [Install](https://www.python.org/downloads/)
- Node.js 18+ → [Install](https://nodejs.org/)
- UV (optional) → `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Bun (optional) → `curl -fsSL https://bun.sh/install | bash`

## 🔧 Troubleshooting

**Port in use?**
```bash
# Backend: Change port
uv run python -m uvicorn api.main:app --port 8002

# Frontend: Change port
PORT=3001 bun run dev
```

**Module not found?**
```bash
# Backend
cd apps/backend && uv sync

# Frontend
cd apps/frontend && bun install
```

## 📚 Next Steps

- **Full Setup Guide**: [SETUP.md](SETUP.md)
- **Contributing**: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- **Documentation**: [docs/](docs/)

---

**Need help?** [Open an issue](https://github.com/adhit-r/fairmind/issues/new) or [join discussions](https://github.com/adhit-r/fairmind/discussions)

