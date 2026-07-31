import logging
import logging.handlers
import os

from flask import Flask, request, jsonify
from markupsafe import escape


def configure_logging() -> None:
    log_path = os.getenv('FLASK_LOG_FILE', 'app.log')
    log_level = logging.DEBUG if os.getenv('FLASK_DEBUG', 'false').lower() in ('1', 'true') else logging.INFO

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8',
    )
    handler.setFormatter(formatter)
    handler.setLevel(log_level)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)


def create_app() -> Flask:
    app = Flask(__name__)

    configure_logging()

    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.exception('Unhandled exception')
        response = {
            'error': 'Internal server error',
            'message': str(error),
        }
        if app.debug:
            response['type'] = type(error).__name__
        return jsonify(response), 500

    @app.get('/')
    def hello() -> str:
        name = request.args.get('name', 'World', type=str).strip()
        if len(name) > 100:
            name = name[:100]
        safe_name = escape(name)
        return f'Hello, {safe_name}!'

    return app


app = create_app()

if __name__ == '__main__':
    app.run(
        host=os.getenv('FLASK_RUN_HOST', '127.0.0.1'),
        port=int(os.getenv('FLASK_RUN_PORT', '5000')),
        debug=os.getenv('FLASK_DEBUG', 'false').lower() in ('1', 'true'),
    )