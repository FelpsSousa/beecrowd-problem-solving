# Development Setup

Verify everything works after setup:

```bash
python scripts/check_all.py --all
```

## Required tools

- Python 3.9+
- g++ / gcc (C++17/20 and C17)
- Node.js (JavaScript solutions)
- Rust via `rustup` (optional, local study only; see [Language Policy](language-policy.md))
- Git and the [GitHub CLI](https://cli.github.com/) (`gh`)

## Windows

```powershell
choco install mingw -y
winget install -e --id Python.Python.3.12
winget install -e --id OpenJS.NodeJS.LTS
winget install -e --id Rustlang.Rustup
```

Open a **new** terminal window afterward: PATH changes do not reach windows already open.

## Linux (Debian/Ubuntu)

```
sudo apt update
sudo apt install -y build-essential python3 nodejs npm
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

## One-time per clone

```
git config core.hooksPath scripts/hooks
git update-index --chmod=+x scripts/hooks/pre-commit scripts/hooks/pre-push
```

See [Testing](testing.md) for what each check does, and [Coding Standards](coding-standards.md) for the rules they enforce.