"""Local Codex workflow; importing this module never starts an analysis."""
from cli.local import main

if __name__ == "__main__":
    raise SystemExit(main())
