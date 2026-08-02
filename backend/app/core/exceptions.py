class AppException(Exception):
    """Base application exception."""
    
    def __init__(self, message: str, status_code: int = 400, code: str = "BAD_REQUEST"):
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


class NotFoundError(AppException):
    """Resource not found."""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404, code="NOT_FOUND")


class ValidationError(AppException):
    """Validation error."""
    
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=400, code="VALIDATION_ERROR")


class StorageError(AppException):
    """Storage error."""
    
    def __init__(self, message: str = "Storage error"):
        super().__init__(message, status_code=500, code="STORAGE_ERROR")


class ProcessingError(AppException):
    """Image processing error."""
    
    def __init__(self, message: str = "Processing error"):
        super().__init__(message, status_code=500, code="PROCESSING_ERROR")