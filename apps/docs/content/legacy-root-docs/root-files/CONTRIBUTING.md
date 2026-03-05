# Contributing to FairMind

First off, thanks for taking the time to contribute! :tada:

The following is a set of guidelines for contributing to FairMind and its packages. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

## Code of Conduct

This project and everyone participating in it is governed by the [FairMind Code of Conduct](../CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to support@fairmind.xyz.

## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report for FairMind. Following these guidelines helps maintainers and the community understand your report, reproduce the behavior, and find related reports.

- **Use a clear and descriptive title** for the issue to identify the problem.
- **Describe the exact steps which reproduce the problem** in as many details as possible.
- **Provide specific examples to demonstrate the steps**. Include links to files or GitHub projects, or copy/pasteable snippets, which you use in those examples.
- **Describe the behavior you observed after following the steps** and point out what exactly is the problem with that behavior.
- **Explain which behavior you expected to see instead and why.**
- **Include screenshots and formatted logs** which you can find in your terminal or console.

[Open a Bug Report](https://github.com/adhit-r/fairmind/issues/new?assignees=&labels=bug&template=bug_report.yml&title=%5BBUG%5D%3A+)

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for FairMind, including completely new features and minor improvements to existing functionality.

- **Use a clear and descriptive title** for the issue to identify the suggestion.
- **Provide a step-by-step description of the suggested enhancement** in as many details as possible.
- **Explain why this enhancement would be useful** to most FairMind users.

[Open a Feature Request](https://github.com/adhit-r/fairmind/issues/new?assignees=&labels=enhancement&template=feature_request.yml&title=%5BFEAT%5D%3A+)

### Pull Requests

The process described here has several goals:
- Maintain FairMind's quality
- Fix problems that are important to users
- Engage the community in working toward the best possible FairMind

1.  **Fork the repository** and create your branch from `main`.
2.  **Clone the repository** locally.
    ```bash
    git clone https://github.com/YOUR_USERNAME/fairmind.git
    cd fairmind
    ```
3.  **Setup Development Environment**:
    - Backend: Python 3.9+ (`uv` recommended)
    - Frontend: Node.js 18+ (`bun` recommended)
    - See [SETUP.md](../SETUP.md) for detailed instructions.
4.  **Make sure your code lints and tests pass**.
    - Backend: `uv run pytest`
    - Frontend: `bun test`
5.  **Commit your changes** using [Conventional Commits](https://www.conventionalcommits.org/).
    - `feat: add new bias metric`
    - `fix: resolve login issue`
    - `docs: update readme`
6.  **Push to your fork** and submit a Pull Request.

## Styleguides

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

### Python Styleguide

- We use `black` for formatting and `isort` for import sorting.
- Type hints are required for all new code.
- Docstrings are required for all public functions and classes.

### TypeScript/React Styleguide

- We use `eslint` and `prettier`.
- Functional components are preferred.
- Use strict type checking.

## Community

- Join our [Discord](https://discord.gg/fairmind) (Coming soon)
- Check out "Good First Issues" on our [Project Board](https://github.com/adhit-r/fairmind/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).
