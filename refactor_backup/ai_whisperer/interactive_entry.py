"""
Entry point for starting the interactive server from the CLI.
"""
import sys
import subprocess

def main():
    """Start the interactive_server.main module as a subprocess."""
    try:
        print("Starting AIWhisperer interactive server...")
        subprocess.run([sys.executable, "-m", "interactive_server.main"], check=True)
    except KeyboardInterrupt:
        print("\nInteractive server stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting interactive server: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
