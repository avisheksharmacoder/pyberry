from pyberry.core.responses import HTTPException
from pyberry import status

class BadRequestException(HTTPException):
    def __init__(self, detail: str = "Bad Request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

class PaymentRequiredException(HTTPException):
    def __init__(self, detail: str = "Payment Required"):
        super().__init__(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=detail)

class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Not Found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class MethodNotAllowedException(HTTPException):
    def __init__(self, detail: str = "Method Not Allowed"):
        super().__init__(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail=detail)

class NotAcceptableException(HTTPException):
    def __init__(self, detail: str = "Not Acceptable"):
        super().__init__(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=detail)

class ProxyAuthenticationRequiredException(HTTPException):
    def __init__(self, detail: str = "Proxy Authentication Required"):
        super().__init__(status_code=status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED, detail=detail)

class RequestTimeoutException(HTTPException):
    def __init__(self, detail: str = "Request Timeout"):
        super().__init__(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail=detail)

class ConflictException(HTTPException):
    def __init__(self, detail: str = "Conflict"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

class GoneException(HTTPException):
    def __init__(self, detail: str = "Gone"):
        super().__init__(status_code=status.HTTP_410_GONE, detail=detail)

class LengthRequiredException(HTTPException):
    def __init__(self, detail: str = "Length Required"):
        super().__init__(status_code=status.HTTP_411_LENGTH_REQUIRED, detail=detail)

class PreconditionFailedException(HTTPException):
    def __init__(self, detail: str = "Precondition Failed"):
        super().__init__(status_code=status.HTTP_412_PRECONDITION_FAILED, detail=detail)

class RequestEntityTooLargeException(HTTPException):
    def __init__(self, detail: str = "Request Entity Too Large"):
        super().__init__(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=detail)

class RequestURITooLongException(HTTPException):
    def __init__(self, detail: str = "Request-URI Too Long"):
        super().__init__(status_code=status.HTTP_414_REQUEST_URI_TOO_LONG, detail=detail)

class UnsupportedMediaTypeException(HTTPException):
    def __init__(self, detail: str = "Unsupported Media Type"):
        super().__init__(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=detail)

class RequestedRangeNotSatisfiableException(HTTPException):
    def __init__(self, detail: str = "Requested Range Not Satisfiable"):
        super().__init__(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE, detail=detail)

class ExpectationFailedException(HTTPException):
    def __init__(self, detail: str = "Expectation Failed"):
        super().__init__(status_code=status.HTTP_417_EXPECTATION_FAILED, detail=detail)

class ImATeapotException(HTTPException):
    def __init__(self, detail: str = "I'm a teapot"):
        super().__init__(status_code=status.HTTP_418_IM_A_TEAPOT, detail=detail)

class MisdirectedRequestException(HTTPException):
    def __init__(self, detail: str = "Misdirected Request"):
        super().__init__(status_code=status.HTTP_421_MISDIRECTED_REQUEST, detail=detail)

class UnprocessableEntityException(HTTPException):
    def __init__(self, detail: str = "Unprocessable Entity"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)

class LockedException(HTTPException):
    def __init__(self, detail: str = "Locked"):
        super().__init__(status_code=status.HTTP_423_LOCKED, detail=detail)

class FailedDependencyException(HTTPException):
    def __init__(self, detail: str = "Failed Dependency"):
        super().__init__(status_code=status.HTTP_424_FAILED_DEPENDENCY, detail=detail)

class TooEarlyException(HTTPException):
    def __init__(self, detail: str = "Too Early"):
        super().__init__(status_code=status.HTTP_425_TOO_EARLY, detail=detail)

class UpgradeRequiredException(HTTPException):
    def __init__(self, detail: str = "Upgrade Required"):
        super().__init__(status_code=status.HTTP_426_UPGRADE_REQUIRED, detail=detail)

class PreconditionRequiredException(HTTPException):
    def __init__(self, detail: str = "Precondition Required"):
        super().__init__(status_code=status.HTTP_428_PRECONDITION_REQUIRED, detail=detail)

class TooManyRequestsException(HTTPException):
    def __init__(self, detail: str = "Too Many Requests"):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)

class RequestHeaderFieldsTooLargeException(HTTPException):
    def __init__(self, detail: str = "Request Header Fields Too Large"):
        super().__init__(status_code=status.HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE, detail=detail)

class UnavailableForLegalReasonsException(HTTPException):
    def __init__(self, detail: str = "Unavailable For Legal Reasons"):
        super().__init__(status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS, detail=detail)

class InternalServerErrorException(HTTPException):
    def __init__(self, detail: str = "Internal Server Error"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

class NotImplementedException(HTTPException):
    def __init__(self, detail: str = "Not Implemented"):
        super().__init__(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=detail)

class BadGatewayException(HTTPException):
    def __init__(self, detail: str = "Bad Gateway"):
        super().__init__(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)

class ServiceUnavailableException(HTTPException):
    def __init__(self, detail: str = "Service Unavailable"):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

class GatewayTimeoutException(HTTPException):
    def __init__(self, detail: str = "Gateway Timeout"):
        super().__init__(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=detail)

class HTTPVersionNotSupportedException(HTTPException):
    def __init__(self, detail: str = "HTTP Version Not Supported"):
        super().__init__(status_code=status.HTTP_505_HTTP_VERSION_NOT_SUPPORTED, detail=detail)

class VariantAlsoNegotiatesException(HTTPException):
    def __init__(self, detail: str = "Variant Also Negotiates"):
        super().__init__(status_code=status.HTTP_506_VARIANT_ALSO_NEGOTIATES, detail=detail)

class InsufficientStorageException(HTTPException):
    def __init__(self, detail: str = "Insufficient Storage"):
        super().__init__(status_code=status.HTTP_507_INSUFFICIENT_STORAGE, detail=detail)

class LoopDetectedException(HTTPException):
    def __init__(self, detail: str = "Loop Detected"):
        super().__init__(status_code=status.HTTP_508_LOOP_DETECTED, detail=detail)

class NotExtendedException(HTTPException):
    def __init__(self, detail: str = "Not Extended"):
        super().__init__(status_code=status.HTTP_510_NOT_EXTENDED, detail=detail)

class NetworkAuthenticationRequiredException(HTTPException):
    def __init__(self, detail: str = "Network Authentication Required"):
        super().__init__(status_code=status.HTTP_511_NETWORK_AUTHENTICATION_REQUIRED, detail=detail)
