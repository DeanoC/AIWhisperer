
import pytest
import subprocess
import socket
import sys
import time

@pytest.fixture(scope="session")
def start_interactive_server():
    """
    Start the interactive server in a subprocess for integration/performance tests.
    Waits for the server to be ready, then yields. Kills the server after tests.
    """
    # Start the server
    proc = subprocess.Popen([
        sys.executable, "-m", "interactive_server.main"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        # Wait for the server to be ready
        for _ in range(30):
            try:
                with socket.create_connection(("127.0.0.1", 8000), timeout=1):
                    break
            except (ConnectionRefusedError, OSError):
                time.sleep(1)
        else:
            proc.terminate()
            raise RuntimeError("Interactive server did not start in time.")

        yield

    finally:
        # Ensure proper cleanup of the subprocess and its pipes
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        
        # Close the pipes to avoid resource warnings
        if proc.stdout:
            proc.stdout.close()
        if proc.stderr:
            proc.stderr.close()
import pytest
import threading
import asyncio
import sys
import time

@pytest.fixture(scope="session", autouse=True)
def cleanup_threads_and_event_loops():
    def log_threads(label):
        print(f"\n[DIAGNOSTIC] {label}: Active threads:")
        for t in threading.enumerate():
            print(f"  - {t.name} (daemon={t.daemon}, ident={t.ident}, alive={t.is_alive()}, target={getattr(t, '_target', None)})")
    log_threads("START of test session")
    yield
    log_threads("END of test session (before join)")
    main_thread = threading.current_thread()
    for t in threading.enumerate():
        if t is main_thread or t.daemon:
            continue
        if t.is_alive():
            print(f"[DIAGNOSTIC] Joining thread: {t.name}")
            try:
                t.join(timeout=2)
            except Exception as e:
                print(f"[DIAGNOSTIC] Exception joining thread {t.name}: {e}")
    log_threads("END of test session (after join)")
    # Try to close any running asyncio event loops
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and not loop.is_closed():
            print("[DIAGNOSTIC] Closing asyncio event loop...")
            loop.stop()
            loop.close()
    except Exception as e:
        print(f"[DIAGNOSTIC] Exception closing event loop: {e}")
    # For Python 3.10+, also shut down default executor
    if sys.version_info >= (3, 10):
        try:
            asyncio.get_running_loop().shutdown_default_executor()
        except Exception as e:
            print(f"[DIAGNOSTIC] Exception shutting down default executor: {e}")
    # Wait a moment and print threads again
    time.sleep(1)
    log_threads("FINAL thread state after cleanup")
