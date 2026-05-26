TIME_BUCKET_LABELS_ID = {
    "morning": "pagi",
    "afternoon": "siang",
    "evening": "sore",
    "night": "malam",
}


def time_bucket_label_id(bucket: str | None) -> str | None:
    if not bucket:
        return None
    return TIME_BUCKET_LABELS_ID.get(bucket, bucket)
