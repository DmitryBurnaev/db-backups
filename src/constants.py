from enum import StrEnum


class BackupLocation(StrEnum):
    S3 = "S3"
    LOCAL = "LOCAL"
    FILE = "FILE"


class BackupHandler(StrEnum):
    MYSQL = "MYSQL"
    PG_SERVICE = "PG"
    PG_CONTAINER = "PG_CONTAINER"


ENV_VARS_REQUIRES = {
    "S3": (
        "S3_REGION_NAME",
        "S3_STORAGE_URL",
        "S3_ACCESS_KEY_ID",
        "S3_SECRET_ACCESS_KEY",
        "S3_BUCKET_NAME",
        "S3_PATH",
    ),
    "LOCAL_PATH": ("LOCAL_PATH",),
    "ENCRYPT": ("ENCRYPT_PASS",),
}
BACKUP_LOCATIONS = tuple(BackupLocation.__members__.keys())
