from fastapi.responses import JSONResponse, Response

def success_response(message: str = "Success", data: dict = {}, status_code: int = 200, **more_info) -> JSONResponse:
    """
    Generates a JSON response for successful operations.

    Args:
        message (str, optional): A message describing the success. Defaults to "Success".
        data (dict, optional): The data to include in the response. Defaults to an empty dictionary.
        status_code (int, optional): The HTTP status code for the response. Defaults to 200.
        **more_info: Additional keyword arguments to include in the response.

    Returns:
        JSONResponse: A FastAPI JSONResponse object with the provided data and status code.
    """
    
    # if status code is 204, no content should be returned
    if status_code == 204:
        return Response(status_code=status_code)
    
    response = {
        "message": message,
        "data": data,
        **more_info,
    }
    return JSONResponse(content=response, status_code=status_code)

def error_response(message: str, status_code: int = 400, **more_info: dict) -> JSONResponse:
    """
    Generates a JSON response for error situations.

    Args:
        message (str): A message describing the error.
        status_code (int, optional): The HTTP status code for the response. Defaults to 400.
        **more_info: Additional keyword arguments to include in the response.

    Returns:
        JSONResponse: A FastAPI JSONResponse object with the provided error message and status code.
    """
    response = {
        "error": {
            "message": message,
            **more_info,
        }
    }
    return JSONResponse(content=response, status_code=status_code)

# 200 for successful GET requests
# 201 for successful POST requests that create a new resource
# 204 for successful DELETE requests
# 400 for bad requests (invalid input)
# 401 for authentication failures
# 403 for authorization failures
# 404 for requests to non-existent resources
# 409 for conflicts (e.g., resource already exists)
# 422 for requests that is in an understandable format but having semantic errors
# 500 for unexpected server errors