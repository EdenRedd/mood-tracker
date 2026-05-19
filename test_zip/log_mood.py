import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore
    ClientError = Exception  # type: ignore

TABLE_NAME = "mood-tracker"
DEFAULT_REGION = os.getenv("AWS_REGION", "us-east-2")


def get_dynamodb_resource():
    if boto3 is None:
        raise ImportError("boto3 is required. Install with `pip install boto3`.")
    return boto3.resource("dynamodb", region_name=DEFAULT_REGION)


def create_mood_table(dynamodb=None):
    dynamodb = dynamodb or get_dynamodb_resource()
    table = dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "entry_date", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "entry_date", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()
    return table


def get_mood_table():
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(TABLE_NAME)
    try:
        table.load()
    except ClientError as error:
        logger.exception("DynamoDB client error while loading table %s", TABLE_NAME)
        code = error.response.get("Error", {}).get("Code")
        if code in ("ResourceNotFoundException", "ValidationException"):
            return create_mood_table(dynamodb)
        raise
    except Exception:
        logger.exception("Unexpected error while loading table %s", TABLE_NAME)
        # If a non-ClientError occurs (various boto/botocore setups or local DynamoDB),
        # attempt to create the table as a fallback rather than failing outright.
        return create_mood_table(dynamodb)
    return table


def normalize_entry_date(entry_date: str | None = None) -> str:
    if not entry_date:
        return datetime.now(timezone.utc).date().isoformat()
    try:
        parsed = datetime.fromisoformat(entry_date)
    except ValueError as error:
        logger.error("Invalid entry_date format: %s", entry_date, exc_info=True)
        raise ValueError("date must be ISO format YYYY-MM-DD") from error
    return parsed.date().isoformat()


def log_mood(user_id: str, mood: str, entry_date: str | None = None) -> Dict[str, Any]:
    if not user_id:
        raise ValueError("user_id is required")
    if not mood or not isinstance(mood, str):
        raise ValueError("mood is required and must be a string")

    entry_date = normalize_entry_date(entry_date)
    table = get_mood_table()
    item = {
        "user_id": user_id,
        "entry_date": entry_date,
        "mood": mood,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    logger.info("Writing mood item: user_id=%s entry_date=%s mood=%s", user_id, entry_date, mood)
    try:
        table.put_item(Item=item)
    except Exception:
        logger.exception("Failed to put item into DynamoDB for user_id=%s entry_date=%s", user_id, entry_date)
        raise
    return item
