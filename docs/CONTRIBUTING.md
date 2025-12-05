# Contributing to FairMind

Thank you for your interest in contributing to FairMind! We welcome contributions from the community to help make AI more fair, transparent, and compliant.

## Getting Started

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** locally:
    ```bash
    git clone https://github.com/YOUR_USERNAME/fairmind.git
    cd fairmind
    ```
3.  **Set up the environment**:
    *   Backend: Python 3.9+ (using `uv`)
    *   Frontend: Node.js 18+ (using `bun`)
    *   See [GETTING_STARTED.md](./GETTING_STARTED.md) for detailed instructions.

## Development Workflow

1.  **Create a branch** for your feature or fix:
    ```bash
    git checkout -b feature/my-new-feature
    ```
2.  **Make your changes**.
3.  **Run tests**:
    *   Backend: `pytest`
    *   Frontend: `bun test`
4.  **Commit your changes** using conventional commits (e.g., `feat: add new bias metric`, `fix: resolve login issue`).
5.  **Push to your fork** and submit a **Pull Request**.

## Project Structure

*   `apps/backend`: FastAPI backend service.
*   `apps/frontend`: Next.js frontend application.
*   `apps/website`: Marketing website (Astro).
*   `docs`: Project documentation.

## Code Style

*   **Python**: We use `black` and `isort`.
*   **TypeScript**: We use `eslint` and `prettier`.

## Community

*   Join our [Discord](https://discord.gg/fairmind) (placeholder).
*   Check out "Good First Issues" on our [Project Board](https://github.com/orgs/fairmind/projects/1).
