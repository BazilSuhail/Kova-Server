import os
import sys

# Windows consoles default to a legacy codepage (cp1252); without this the
# startup banners and any non-ASCII output crash the process whenever stdout
# is redirected (CI, service managers, `> server.log`). Idempotent + safe.
for _stream in (sys.stdout, sys.stderr):
    _reconfigure = getattr(_stream, "reconfigure", None)
    if _reconfigure is not None:
        _reconfigure(encoding="utf-8", errors="replace")

# Imports come after the stream fix on purpose: UTF-8 must be in place before
# anything (including app logging setup) writes to stdout on Windows.
from app import create_app  # noqa: E402

# Create the Flask app instance
app = create_app()

def run_development():
    """Run development server with Waitress (same as production but with more logging)"""
    try:
        from waitress import serve

        port = int(os.environ.get('PORT', 5000))
        host = '0.0.0.0'
        threads = int(os.environ.get("KOVA_WEB_THREADS", "4"))

        print("Starting Kova development server with Waitress...")
        print("✅ Using same server as production (Waitress)")
        print("🔧 Development mode - detailed logging enabled")
        print("🚀 Development server ready at:")
        print(f"   - Local: http://127.0.0.1:{port}")
        print(f"   - Network: http://192.168.100.16:{port}")
        print("\nPress Ctrl+C to stop the server")
        print("-" * 50)

        serve(
            app,
            host=host,
            port=port,
            threads=threads,           # Tunable via KOVA_WEB_THREADS
            connection_limit=100,     # Lower connection limit for dev
            cleanup_interval=10,      # More frequent cleanup for dev
            channel_timeout=60,       # Shorter timeout for dev
            expose_tracebacks=True    # Show tracebacks in development
        )
    except ImportError:
        print("❌ Waitress not installed.")
        print("Install with: pip install waitress")
        sys.exit(1)

def run_flask_debug():
    """Run original Flask development server (with auto-reload)"""
    print("Starting Kova with Flask debug server...")
    print("⚠️  Development server warning will appear")
    print("🔄 Auto-reload enabled - files changes will restart server")
    app.run(debug=True, host="0.0.0.0", port=5000)

def run_production():
    """Run production server with Waitress"""
    try:
        from waitress import serve

        # Get port from environment (Railway, Heroku, etc.) or default to 5000
        port = int(os.environ.get('PORT', 5000))
        host = '0.0.0.0'
        threads = int(os.environ.get("KOVA_WEB_THREADS", "3"))

        print("Starting Kova production server...")
        print("✅ No development server warnings!")
        print("🚀 Production server ready at:")
        print(f"   - Host: {host}")
        print(f"   - Port: {port}")

        # Check if running on Railway
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            print("🚂 Detected Railway deployment")

        print("\nPress Ctrl+C to stop the server")

        serve(
            app,
            host=host,
            port=port,
            threads=threads,            # Tunable via KOVA_WEB_THREADS (default 3)
            connection_limit=1000,    # Max 1000 connections
            cleanup_interval=30,      # Cleanup every 30 seconds
            channel_timeout=120,      # 2 minute timeout
            expose_tracebacks=False   # Don't expose tracebacks in production
        )
    except ImportError:
        print("❌ Waitress not installed.")
        print("Install with: pip install waitress")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Server stopped gracefully")

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--production' or sys.argv[1] == '-p':
            run_production()
        elif sys.argv[1] == '--development' or sys.argv[1] == '-d':
            run_development()
        elif sys.argv[1] == '--flask-debug' or sys.argv[1] == '-f':
            run_flask_debug()
        elif sys.argv[1] == '--help' or sys.argv[1] == '-h':
            print("Kova Server Runner")
            print("Usage:")
            print("  python run.py                    # Development mode with Waitress (default)")
            print("  python run.py --production       # Production mode")
            print("  python run.py -p                 # Production mode (short)")
            print("  python run.py --development      # Development mode with Waitress")
            print("  python run.py -d                 # Development mode (short)")
            print("  python run.py --flask-debug      # Flask debug server (auto-reload)")
            print("  python run.py -f                 # Flask debug server (short)")
            sys.exit(0)
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use --help for available options")
            sys.exit(1)

    # Check environment variable or Railway deployment
    elif os.environ.get('FLASK_ENV') == 'production' or os.environ.get('RAILWAY_ENVIRONMENT'):
        run_production()

    # Default to development
    else:
        run_development()
# from app import create_app

# app = create_app()

# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=5000)
