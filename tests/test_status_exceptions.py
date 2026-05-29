import pytest
from pyberry import status
from pyberry import exceptions
from pyberry.core.rsgi import app, router
from conftest import MockRSGIScope, MockRSGIProtocol
from pyberry.db import db
from unittest.mock import Mock

@pytest.fixture(autouse=True)
def mock_db_init(monkeypatch):
    monkeypatch.setattr(db, "init_db", Mock())

def test_all_status_codes():
    # 1xx
    assert status.HTTP_100_CONTINUE == 100
    assert status.HTTP_101_SWITCHING_PROTOCOLS == 101
    assert status.HTTP_102_PROCESSING == 102
    assert status.HTTP_103_EARLY_HINTS == 103

    # 2xx
    assert status.HTTP_200_OK == 200
    assert status.HTTP_201_CREATED == 201
    assert status.HTTP_202_ACCEPTED == 202
    assert status.HTTP_203_NON_AUTHORITATIVE_INFORMATION == 203
    assert status.HTTP_204_NO_CONTENT == 204
    assert status.HTTP_205_RESET_CONTENT == 205
    assert status.HTTP_206_PARTIAL_CONTENT == 206
    assert status.HTTP_207_MULTI_STATUS == 207
    assert status.HTTP_208_ALREADY_REPORTED == 208
    assert status.HTTP_226_IM_USED == 226

    # 3xx
    assert status.HTTP_300_MULTIPLE_CHOICES == 300
    assert status.HTTP_301_MOVED_PERMANENTLY == 301
    assert status.HTTP_302_FOUND == 302
    assert status.HTTP_303_SEE_OTHER == 303
    assert status.HTTP_304_NOT_MODIFIED == 304
    assert status.HTTP_305_USE_PROXY == 305
    assert status.HTTP_306_RESERVED == 306
    assert status.HTTP_307_TEMPORARY_REDIRECT == 307
    assert status.HTTP_308_PERMANENT_REDIRECT == 308

    # 4xx
    assert status.HTTP_400_BAD_REQUEST == 400
    assert status.HTTP_401_UNAUTHORIZED == 401
    assert status.HTTP_402_PAYMENT_REQUIRED == 402
    assert status.HTTP_403_FORBIDDEN == 403
    assert status.HTTP_404_NOT_FOUND == 404
    assert status.HTTP_405_METHOD_NOT_ALLOWED == 405
    assert status.HTTP_406_NOT_ACCEPTABLE == 406
    assert status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED == 407
    assert status.HTTP_408_REQUEST_TIMEOUT == 408
    assert status.HTTP_409_CONFLICT == 409
    assert status.HTTP_410_GONE == 410
    assert status.HTTP_411_LENGTH_REQUIRED == 411
    assert status.HTTP_412_PRECONDITION_FAILED == 412
    assert status.HTTP_413_REQUEST_ENTITY_TOO_LARGE == 413
    assert status.HTTP_414_REQUEST_URI_TOO_LONG == 414
    assert status.HTTP_415_UNSUPPORTED_MEDIA_TYPE == 415
    assert status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE == 416
    assert status.HTTP_417_EXPECTATION_FAILED == 417
    assert status.HTTP_418_IM_A_TEAPOT == 418
    assert status.HTTP_421_MISDIRECTED_REQUEST == 421
    assert status.HTTP_422_UNPROCESSABLE_ENTITY == 422
    assert status.HTTP_423_LOCKED == 423
    assert status.HTTP_424_FAILED_DEPENDENCY == 424
    assert status.HTTP_425_TOO_EARLY == 425
    assert status.HTTP_426_UPGRADE_REQUIRED == 426
    assert status.HTTP_428_PRECONDITION_REQUIRED == 428
    assert status.HTTP_429_TOO_MANY_REQUESTS == 429
    assert status.HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE == 431
    assert status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS == 451

    # 5xx
    assert status.HTTP_500_INTERNAL_SERVER_ERROR == 500
    assert status.HTTP_501_NOT_IMPLEMENTED == 501
    assert status.HTTP_502_BAD_GATEWAY == 502
    assert status.HTTP_503_SERVICE_UNAVAILABLE == 503
    assert status.HTTP_504_GATEWAY_TIMEOUT == 504
    assert status.HTTP_505_HTTP_VERSION_NOT_SUPPORTED == 505
    assert status.HTTP_506_VARIANT_ALSO_NEGOTIATES == 506
    assert status.HTTP_507_INSUFFICIENT_STORAGE == 507
    assert status.HTTP_508_LOOP_DETECTED == 508
    assert status.HTTP_510_NOT_EXTENDED == 510
    assert status.HTTP_511_NETWORK_AUTHENTICATION_REQUIRED == 511

def test_all_exceptions_initialization():
    exception_map = {
        exceptions.BadRequestException: (400, "Bad Request"),
        exceptions.UnauthorizedException: (401, "Unauthorized"),
        exceptions.PaymentRequiredException: (402, "Payment Required"),
        exceptions.ForbiddenException: (403, "Forbidden"),
        exceptions.NotFoundException: (404, "Not Found"),
        exceptions.MethodNotAllowedException: (405, "Method Not Allowed"),
        exceptions.NotAcceptableException: (406, "Not Acceptable"),
        exceptions.ProxyAuthenticationRequiredException: (407, "Proxy Authentication Required"),
        exceptions.RequestTimeoutException: (408, "Request Timeout"),
        exceptions.ConflictException: (409, "Conflict"),
        exceptions.GoneException: (410, "Gone"),
        exceptions.LengthRequiredException: (411, "Length Required"),
        exceptions.PreconditionFailedException: (412, "Precondition Failed"),
        exceptions.RequestEntityTooLargeException: (413, "Request Entity Too Large"),
        exceptions.RequestURITooLongException: (414, "Request-URI Too Long"),
        exceptions.UnsupportedMediaTypeException: (415, "Unsupported Media Type"),
        exceptions.RequestedRangeNotSatisfiableException: (416, "Requested Range Not Satisfiable"),
        exceptions.ExpectationFailedException: (417, "Expectation Failed"),
        exceptions.ImATeapotException: (418, "I'm a teapot"),
        exceptions.MisdirectedRequestException: (421, "Misdirected Request"),
        exceptions.UnprocessableEntityException: (422, "Unprocessable Entity"),
        exceptions.LockedException: (423, "Locked"),
        exceptions.FailedDependencyException: (424, "Failed Dependency"),
        exceptions.TooEarlyException: (425, "Too Early"),
        exceptions.UpgradeRequiredException: (426, "Upgrade Required"),
        exceptions.PreconditionRequiredException: (428, "Precondition Required"),
        exceptions.TooManyRequestsException: (429, "Too Many Requests"),
        exceptions.RequestHeaderFieldsTooLargeException: (431, "Request Header Fields Too Large"),
        exceptions.UnavailableForLegalReasonsException: (451, "Unavailable For Legal Reasons"),
        exceptions.InternalServerErrorException: (500, "Internal Server Error"),
        exceptions.NotImplementedException: (501, "Not Implemented"),
        exceptions.BadGatewayException: (502, "Bad Gateway"),
        exceptions.ServiceUnavailableException: (503, "Service Unavailable"),
        exceptions.GatewayTimeoutException: (504, "Gateway Timeout"),
        exceptions.HTTPVersionNotSupportedException: (505, "HTTP Version Not Supported"),
        exceptions.VariantAlsoNegotiatesException: (506, "Variant Also Negotiates"),
        exceptions.InsufficientStorageException: (507, "Insufficient Storage"),
        exceptions.LoopDetectedException: (508, "Loop Detected"),
        exceptions.NotExtendedException: (510, "Not Extended"),
        exceptions.NetworkAuthenticationRequiredException: (511, "Network Authentication Required"),
    }

    for exc_class, (expected_status, expected_detail) in exception_map.items():
        exc = exc_class()
        assert exc.status_code == expected_status
        assert exc.detail == expected_detail
        
        # Test custom detail
        exc_custom = exc_class("Custom Message")
        assert exc_custom.status_code == expected_status
        assert exc_custom.detail == "Custom Message"

@pytest.mark.asyncio
async def test_rsgi_specific_http_exception(mock_proto):
    def handler(req):
        raise exceptions.NotFoundException("Resource 123 not found")
        
    router.add_python_route("GET", "/test_specific_exception", handler)
        
    scope = MockRSGIScope(method="GET", path="/test_specific_exception", proto="http")
    await app(scope, mock_proto)
    
    assert mock_proto.response_called
    assert mock_proto.response_status == 404
    assert mock_proto.response_body == "Resource 123 not found"
