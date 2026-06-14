import json
from pathlib import Path


VALID_CHANNELS = {"notice", "letter"}


def load_local_notices(path="data/notices_fallback.json"):
    try:
        raw_notices = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(raw_notices, list):
        return []

    notices = []
    for raw_notice in raw_notices:
        notice = normalize_notice(raw_notice)
        if notice is not None:
            notices.append(notice)
    return sort_notices(notices)


def normalize_notice(raw_notice):
    if not isinstance(raw_notice, dict):
        return None

    notice_id = str(raw_notice.get("id", "")).strip()
    body = str(raw_notice.get("body", "")).strip()
    channel = str(raw_notice.get("channel", "")).strip()
    if not notice_id or not body or channel not in VALID_CHANNELS:
        return None

    title = str(raw_notice.get("title", notice_id)).strip() or notice_id
    return {
        "id": notice_id,
        "channel": channel,
        "type": str(raw_notice.get("type", "notice")).strip() or "notice",
        "title": title,
        "sender": str(raw_notice.get("sender", "Unknown sender")).strip() or "Unknown sender",
        "date": str(raw_notice.get("date", "-")).strip() or "-",
        "body": body,
        "important": raw_notice.get("important") is True,
    }


def get_notices_by_channel(notices, channel):
    if channel not in VALID_CHANNELS or not isinstance(notices, list):
        return []
    return [notice for notice in notices if isinstance(notice, dict) and notice.get("channel") == channel]


def sort_notices(notices):
    if not isinstance(notices, list):
        return []
    return sorted(
        [notice for notice in notices if isinstance(notice, dict)],
        key=lambda notice: (str(notice.get("date", "")), str(notice.get("id", ""))),
        reverse=True,
    )
