import base64
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    from .edit_mood import update_mood
    from .log_mood import log_mood
except ImportError:
    from edit_mood import update_mood
    from log_mood import log_mood

PATH_PATTERN = re.compile(r"^/users/(?P<user_id>[^/]+)/moods$")


def _build_response(status_code: int, body: Any) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def _normalize_body(event: Dict[str, Any]) -> Dict[str, Any]:
    body = event.get("body")
    if body is None:
        return {}
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")
    try:
        return json.loads(body)
    except json.JSONDecodeError as error:
        raise ValueError("Request body must be valid JSON") from error


def _extract_user_id(event: Dict[str, Any]) -> Optional[str]:
    path_parameters = event.get("pathParameters") or {}
    user_id = path_parameters.get("user_id") or path_parameters.get("userId")
    if user_id:
        return user_id

    path = event.get("path") or event.get("rawPath", "")
    match = PATH_PATTERN.match(path)
    if match:
        return match.group("user_id")
    return None


def _handle_post(user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    mood = payload.get("mood")
    entry_date = payload.get("date")
    item = log_mood(user_id=user_id, mood=mood, entry_date=entry_date)
    return {
        "statusCode": 201,
        "body": json.dumps({"message": "Mood logged.", "item": item}),
    }


def _handle_put(user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    new_mood = payload.get("mood")
    entry_date = payload.get("date")
    if not entry_date:
        raise ValueError("date is required for editing an existing mood entry")

    item = update_mood(user_id=user_id, entry_date=entry_date, new_mood=new_mood)
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Mood updated.", "item": item}),
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method")
    if method not in {"POST", "PUT"}:
        return _build_response(405, {"error": "Method not allowed"})

    user_id = _extract_user_id(event)
    if not user_id:
        return _build_response(404, {"error": "Missing user_id in path"})

    try:
        payload = _normalize_body(event)
    except ValueError as error:
        return _build_response(400, {"error": str(error)})

    try:
        if method == "POST":
            response = _handle_post(user_id, payload)
        else:
            response = _handle_put(user_id, payload)
        return response
    except ValueError as error:
        return _build_response(400, {"error": str(error)})
    except Exception as error:
        return _build_response(500, {"error": "Failed to save mood.", "details": str(error)})


if __name__ == "__main__":
    year = datetime.now(timezone.utc).year
    user_id = "User#Raul"
    print(f"Running locally: logging 14 days of Sad/happy moods for {user_id} in May {year}.")
    created_items = []
    for day in range(1, 15):
        entry_date = f"{year}-05-{day:02d}"
        mood = "Sad" if day % 2 == 1 else "happy"
        try:
            item = log_mood(user_id=user_id, mood=mood, entry_date=entry_date)
            created_items.append(item)
        except Exception as error:
            print(f"Failed to log mood for {entry_date}: {error}")
    print("Logged entries:", json.dumps(created_items, indent=2))
