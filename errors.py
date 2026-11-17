"""Error handling.

Services raise an ApiError with a message and an HTTP status code. They never
build HTTP responses themselves; the handler registered in app.py turns the
error into JSON.
"""
from flask import jsonify


class ApiError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def api_error(message, status_code):
    """Create an error with a custom message and HTTP status code.

    Usage: raise api_error("book not found", 404)
    """
    return ApiError(message, status_code)


def bad_request(message):
    return api_error(message, 400)


def not_found(message):
    return api_error(message, 404)


def conflict(message):
    return api_error(message, 409)


def error_response(message, status_code):
    """Build the JSON error response the API returns: {"error": message}."""
    return jsonify({"error": message}), status_code


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return error_response(error.message, error.status_code)
