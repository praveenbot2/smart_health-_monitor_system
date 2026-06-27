"""
Smart Health Monitor System
Main Application Entry Point
"""

from app import create_app, socketio
import os
import socket

app = create_app()


def _run_socketio(host, port, debug):
    """Run SocketIO server with consistent options."""
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True
    )


def _is_port_bindable(host, port):
    """Return True if the current process can bind to the requested port."""
    test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        test_sock.bind((host, port))
        return True
    except OSError:
        return False
    finally:
        test_sock.close()

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    fallback_port = int(os.environ.get('PORT_FALLBACK', 5050))
    host = os.environ.get('HOST', '127.0.0.1').strip() or '127.0.0.1'
    debug = os.environ.get('FLASK_DEBUG', 'false').strip().lower() == 'true'

    selected_port = port
    if not _is_port_bindable(host, port):
        if fallback_port == port:
            fallback_port += 1
        print(f"{host}:{port} is unavailable. Using fallback port {fallback_port}.")
        selected_port = fallback_port

    # Run with SocketIO for real-time features
    try:
        _run_socketio(host, selected_port, debug)
    except OSError as exc:
        error_text = str(exc).lower()
        is_bind_error = any(
            text in error_text
            for text in (
                'forbidden by its access permissions',
                'only one usage of each socket address',
                'permission denied'
            )
        ) or getattr(exc, 'winerror', None) in (10013, 10048)

        if not is_bind_error:
            raise

        if fallback_port == port:
            fallback_port += 1

        print(
            f"{host}:{selected_port} is unavailable ({exc}). "
            f"Retrying on {host}:{fallback_port}..."
        )
        _run_socketio(host, fallback_port, debug)
