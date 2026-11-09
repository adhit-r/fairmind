# Licensing

FairMind is open source. Different parts of this repository are under different licenses, chosen so that the libraries you import stay permissive while the platform stays open.

| Path | License | SPDX |
| --- | --- | --- |
| `apps/sdk` (PyPI `fairmind`) | Apache License 2.0, in [`apps/sdk/LICENSE`](apps/sdk/LICENSE) | `Apache-2.0` |
| `apps/cli` (PyPI `fairmind-cli`) | Apache License 2.0, in [`apps/cli/LICENSE`](apps/cli/LICENSE) | `Apache-2.0` |
| `apps/mcp` (PyPI `fairmind-mcp`) | Apache License 2.0, in [`apps/mcp/LICENSE`](apps/mcp/LICENSE) | `Apache-2.0` |
| Everything else, including `apps/backend`, `apps/frontend`, `apps/docs` and `apps/website` | GNU Affero General Public License v3.0, in [`LICENSE`](LICENSE) | `AGPL-3.0-only` |

A directory with its own `LICENSE` file is covered by that file; everything else is covered by the root `LICENSE`.

## What this means in practice

- **Using the SDK, CLI or MCP server** in your own code, open or closed, is permitted under Apache-2.0. Keep the license and notices.
- **Running FairMind** for your own organisation, unmodified or modified, is permitted under the AGPL.
- **Offering a modified FairMind to others over a network** (for example as a hosted service) requires making the modified source available to those users under the AGPL, as its section 13 sets out.

## Commercial license

Axonome offers FairMind under a commercial license for organisations that cannot meet the AGPL's terms, for example to keep modifications private while offering FairMind as a service. Write to adhi.r@axonome.xyz.

## Earlier releases

Releases up to and including `v0.3.1-alpha` were published under the MIT License. Those releases remain available under MIT. The MIT copyright and permission notice that applies to code carried over from them is kept in [`LICENSES/MIT-before-relicense.txt`](LICENSES/MIT-before-relicense.txt).

## Contributions

Contributors sign the [Contributor License Agreement](CLA.md) once, on their first pull request. It lets Axonome distribute contributions under both the open-source licenses above and the commercial license. Contributors keep the copyright in their work.
