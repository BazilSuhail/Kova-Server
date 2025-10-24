"""Kova Server entry point.

Usage:
    python run.py                 # development (Waitress)  [default]
    python run.py --production    # production  (Waitress)
    python run.py --development   # development (Waitress)
    python run.py --flask-debug   # Flask dev server (auto-reload)
    python run.py --help
"""
import os
import sys

# Windows consoles default to a legacy codepage (cp1252); without this the
# startup banner and any non-ASCII output crash the process whenever stdout
# is redirected (CI, service managers, `> server.log`). Idempotent + safe.
for _stream in (sys.stdout, sys.stderr):
    _reconfigure = getattr(_stream, "reconfigure", None)
    if _reconfigure is not None:
        _reconfigure(encoding="utf-8", errors="replace")

# Imports come after the stream fix on purpose: UTF-8 must be in place before
# anything (including app logging setup) writes to stdout on Windows.
from app import create_app  # noqa: E402

BANNER = (
    "\n"
    "========================================================\n"
    "   🌿  K O V A   S E R V E R\n"
    "   Personal AI Life Assistant · REST API\n"
    "========================================================"
)

HELP = """Kova Server Runner

Usage:
  python run.py                 development (Waitress)   [default]
  python run.py --production    production  (Waitress)
  python run.py --development   development (Waitress)
  python run.py --flask-debug   Flask dev server (auto-reload)
  python run.py --help          show this help
"""


def _banner() -> None:
    """Print the banner before the app logs its boot sequence."""
    print(BANNER)
    print()


def _serve(host: str, port: int, threads: int, *, production: bool) -> None:
    """Run Waitress with dev/prod tuning."""
    try:
        from waitress import serve
    except ImportError:
        print("❌ Waitress is not installed. Install it with: pip install waitress")
        sys.exit(1)

    app = create_app()
    print(f"\n🚀 Kova is live at http://127.0.0.1:{port}   (Ctrl+C to stop)\n")

    try:
        serve(
            app,
            host=host,
            port=port,
            threads=threads,
            connection_limit=1000 if production else 100,
            cleanup_interval=30 if production else 10,
            channel_timeout=120 if production else 60,
            expose_tracebacks=not production,
        )
    except KeyboardInterrupt:
        print("\n👋 Kova stopped.")


def run_development() -> None:
    """Development server (Waitress) with verbose logging."""
    _banner()
    _serve(
        "0.0.0.0",
        int(os.environ.get("PORT", 5000)),
        int(os.environ.get("KOVA_WEB_THREADS", "4")),
        production=False,
    )


def run_production() -> None:
    """Production server (Waitress)."""
    _banner()
    _serve(
        "0.0.0.0",
        int(os.environ.get("PORT", 5000)),
        int(os.environ.get("KOVA_WEB_THREADS", "3")),
        production=True,
    )


def run_flask_debug() -> None:
    """Flask development server with auto-reload."""
    _banner()
    app = create_app()
    print("\n🚀 Kova is live at http://127.0.0.1:5000   (auto-reload, Ctrl+C to stop)\n")
    app.run(debug=True, host="0.0.0.0", port=5000)


def main() -> None:
    # Load .env first so it can influence the default mode (matches the old
    # behaviour where the app was built at import time).
    from dotenv import load_dotenv

    load_dotenv()

    argument = sys.argv[1] if len(sys.argv) > 1 else None

    if argument in ("--help", "-h"):
        print(HELP)
        return
    if argument in ("--production", "-p"):
        run_production()
    elif argument in ("--development", "-d"):
        run_development()
    elif argument in ("--flask-debug", "-f"):
        run_flask_debug()
    elif argument is None:
        if (
            os.environ.get("FLASK_ENV") == "production"
            or os.environ.get("RAILWAY_ENVIRONMENT")
        ):
            run_production()
        else:
            run_development()
    else:
        print(f"Unknown argument: {argument}")
        print("Use --help for available options")
        sys.exit(1)


if __name__ == "__main__":
    main()
