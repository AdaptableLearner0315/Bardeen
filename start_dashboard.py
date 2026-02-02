"""Script to start the Research Assistant Dashboard."""

import argparse
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()


def main():
    """Start the dashboard server."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Start the Research Assistant Dashboard")
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on (default: 8000)"
    )
    args = parser.parse_args()

    port = args.port

    print("=" * 80)
    print("Research Assistant Dashboard")
    print("=" * 80)
    print()

    # Check for API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it with: export ANTHROPIC_API_KEY=your_key_here")
        print()
        return 1

    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        print("WARNING: TAVILY_API_KEY not set. Web search will not be available.")
        print("Set it with: export TAVILY_API_KEY=your_key_here")
        print()

    print(f"Starting server on port {port}...")
    print()
    print("Dashboard will be available at:")
    print(f"  http://localhost:{port}")
    print()
    print("API Documentation:")
    print(f"  http://localhost:{port}/docs")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 80)
    print()

    # Import and run
    import uvicorn
    from src.dashboard.backend.app import app

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    sys.exit(main())
