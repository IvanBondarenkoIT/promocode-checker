from enum import StrEnum


class PromocodeStatus(StrEnum):
    ACTIVE = "ACTIVE"
    USED = "USED"


class CampaignStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class CampaignKind(StrEnum):
    """Data scope of a campaign: test data vs real customers."""

    TEST = "TEST"
    LIVE = "LIVE"


class CheckerActionType(StrEnum):
    SCAN_CHECK = "SCAN_CHECK"
    MANUAL_CLOSE = "MANUAL_CLOSE"
    AUTO_CLOSE = "AUTO_CLOSE"


class FraudWarningStatus(StrEnum):
    OPEN = "OPEN"
    REVIEWED = "REVIEWED"
    DISMISSED = "DISMISSED"


class AdminRole(StrEnum):
    ADMIN = "admin"
    VIEWER = "viewer"
