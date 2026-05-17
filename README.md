# mood-tracker

## AWS Lambda handler

The Lambda handler is defined as:

```text
src.main.lambda_handler
```

## POST endpoint

Use API Gateway to route `POST /users/{user_id}/moods` to the Lambda function.

Request example:

```json
{
  "mood": "happy",
  "date": "2026-05-17"
}
```

If `date` is omitted, the current UTC date is used.

## Local testing

You can still run `src/main.py` directly, although it does not provide an HTTP server locally.
