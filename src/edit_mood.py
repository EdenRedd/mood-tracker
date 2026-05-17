import os
from datetime import datetime, timezone
from typing import Any, Dict

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore
    ClientError = Exception  # type: ignore

TABLE_NAME = "mood-tracker"
DEFAULT_REGION = os.getenv("AWS_REGION", "us-east-1")


def get_dynamodb_resource():
    if boto3 is None:
        raise ImportError("boto3 is required. Install with `pip install boto3`.")
    return boto3.resource("dynamodb", region_name=DEFAULT_REGION)


def get_mood_table():
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(TABLE_NAME)
    try:
        table.load()
    except ClientError as error:
        code = error.response.get("Error", {}).get("Code")
        if code in ("ResourceNotFoundException", "ValidationException"):
            raise RuntimeError(f"DynamoDB table '{TABLE_NAME}' does not exist.") from error
        raise
    return table


def normalize_entry_date(entry_date: str | None = None) -> str:
    if not entry_date:
        return datetime.now(timezone.utc).date().isoformat()
    try:
        parsed = datetime.fromisoformat(entry_date)
    except ValueError as error:
        raise ValueError("date must be ISO format YYYY-MM-DD") from error
    return parsed.date().isoformat()


def update_mood(user_id: str, entry_date: str, new_mood: str) -> Dict[str, Any]:
    if not user_id:
        raise ValueError("user_id is required")
    if not entry_date:
        raise ValueError("entry_date is required")
    if not new_mood or not isinstance(new_mood, str):
        raise ValueError("new_mood is required and must be a string")

    entry_date = normalize_entry_date(entry_date)
    table = get_mood_table()
    response = table.update_item(
        Key={"user_id": user_id, "entry_date": entry_date},
        UpdateExpression="SET mood = :new_mood, updated_at = :updated_at",
        ExpressionAttributeValues={
            ":new_mood": new_mood,
            ":updated_at": datetime.now(timezone.utc).isoformat(),
        },
        ConditionExpression="attribute_exists(user_id) AND attribute_exists(entry_date)",
        ReturnValues="ALL_NEW",
    )
    return response.get("Attributes", {})


if __name__ == "__main__":
    print("edit_mood.py provides update_mood(user_id, entry_date, new_mood)")
