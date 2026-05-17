import json
import re
from typing import Any, Dict, List

try:
    from .log_mood import get_mood_table
except ImportError:
    from log_mood import get_mood_table

try:
    from boto3.dynamodb.conditions import Key
except ImportError:
    Key = None  # type: ignore

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")


def _validate_user_id(user_id: str) -> None:
    if not user_id:
        raise ValueError("user_id is required")


def _validate_date(date_value: str) -> str:
    if not date_value:
        raise ValueError("date is required")
    if DATE_PATTERN.match(date_value) or MONTH_PATTERN.match(date_value):
        return date_value
    raise ValueError("date must be in YYYY-MM or YYYY-MM-DD format")


def fetch_moods(user_id: str, date_value: str) -> List[Dict[str, Any]]:
    """Fetch mood entries for a user by exact date or by month."""
    _validate_user_id(user_id)
    date_value = _validate_date(date_value)
    table = get_mood_table()

    if DATE_PATTERN.match(date_value):
        result = table.get_item(Key={"user_id": user_id, "entry_date": date_value})
        item = result.get("Item")
        return [item] if item else []

    if Key is None:
        raise RuntimeError("boto3 is required to query DynamoDB")

    response = table.query(
        KeyConditionExpression=Key("user_id").eq(user_id) & Key("entry_date").begins_with(date_value),
        ScanIndexForward=True,
    )
    return response.get("Items", [])


def fetch_moods_json(user_id: str, date_value: str) -> str:
    moods = fetch_moods(user_id=user_id, date_value=date_value)
    payload = {"user_id": user_id, "date": date_value, "items": moods}
    json_payload = json.dumps(payload)
    print(json_payload)
    return json_payload


if __name__ == "__main__":
    print("month_fetch.py provides fetch_moods(user_id, date_value) and fetch_moods_json(user_id, date_value)")
