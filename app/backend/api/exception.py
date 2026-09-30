from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response
    details = response.data
    if isinstance(details, dict) and "detail" in details:
        message = str(details["detail"])
        details = None
    else:
        message = "Request validation failed" if response.status_code < 500 else "Internal server error"
    response.data = {"error": {"code": response.status_code, "message": message, "details": details}}
    return response

