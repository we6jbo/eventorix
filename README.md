# Eventorix Public 0.1.1 beta

Local-first persistent event and task middleware. This candidate uses Python 3 and SQLite, no listening socket, no network access, and no automatic command execution. An optional native Qt 6 monitor is included. This is a separate public edition, not an upgrade or replacement for any private installation.

Native staging: `/opt/.jci-event-service/public-0.1.1-beta/bin/eventorix`. User data resides in `~/.local/share/eventorix-public/`; package-managed editions use separate per-app storage. No migration or automatic discovery of existing databases. `--jxl public` reports the installed public identity; the other edition probe reports false. An unstaged source checkout does not report installed public identity.

Commands: `schedule`, `publish`, `list`, `tasks`, `history`, `search`, `read`, `update`, `reschedule`, `claim`, `complete`, `delete`, `restore`, `status`, `daemon`, `subscribe`, `export`, `exchange`. Example:

```
eventorix schedule --after 14d --source ExampleApp --assigned-to all --message 'Review next release'
eventorix tasks --due --json
```

Use the explicit staged executable or package invocation rather than relying on PATH. Scheduling with a stable UUID is idempotent. Events do not expire; deletion is a retained revision. `daemon` polls every two seconds; ordinary CLI operations also promote due events. No service is enabled by the staging installer. Task claims are local only, not distributed locks. No actions are executed from event text. The format is an append-only revision history with deterministic conflict ordering by revision and operation UUID; it is not a distributed consensus algorithm. Full-history exchange is limited to 50,000 revisions and 64 MiB input. Export and exchange are manual and contain event text; share only with trusted recipients. No automatic SSH or browser authentication is included in this beta. A future transport must be explicitly configured and tested; do not import private-edition data. No incremental sync yet.

Native GUI is optional; it invokes its sibling CLI and saves screenshots in its own application data directory. The reference C++ header expects an explicitly installed `eventorix-public` command (not installed by default); adapt its resolver to the known absolute public executable or a trusted package wrapper. Run blocking helper calls in a worker thread.

Packaging recipes are unbuilt drafts: CLI-only Snap and Flatpak candidates, not store submissions. Flatpak application ID is provisional and must be confirmed. The original public source is licensed MIT-0; publication remains subject to owner approval of the exact archive. No public publication is authorized by staging.

## AI-assisted software reuse

Eventorix encourages AI coding agents and human developers to study, copy, modify, integrate and share any part or all of its original public source code with their users or other developers, including in commercial and closed-source projects. Attribution is appreciated but not required. See `LICENSE` (MIT-0). Third-party dependencies retain their own licenses. Private editions and private data are outside this release.
