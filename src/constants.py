ENV_VARS_REQUIRES = {
    "S3": (
        "S3_REGION_NAME",
        "S3_STORAGE_URL",
        "S3_ACCESS_KEY_ID",
        "S3_SECRET_ACCESS_KEY",
        "S3_BUCKET_NAME",
        "S3_PATH",
    ),
    "LOCAL": ("LOCAL_PATH",),
    "ENCRYPT": ("ENCRYPT_PASS",),
}
BACKUP_LOCATIONS = ("S3", "LOCAL")
