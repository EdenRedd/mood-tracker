# mood-tracker

## AWS Lambda handler

The Lambda handler is defined as:

```text
lambda_function.lambda_handler
```

## API endpoint

Use API Gateway to route `ANY /mood-tracker` to the Lambda function.

The backend accepts:
  - `GET /mood-tracker?user_id=<id>&date=<YYYY-MM-DD>`
  - `POST /mood-tracker`
  - `PUT /mood-tracker`
  - `OPTIONS /mood-tracker`

Required fields:
  - `user_id` in query string or JSON body
  - `date` in query string or JSON body for GET and PUT

POST example:

```json
{
  "user_id": "Raul",
  "mood": "happy",
  "date": "2026-05-17"
}
```

PUT example:

```json
{
  "user_id": "Raul",
  "mood": "happy",
  "date": "2026-05-19"
}
```

GET example:

```text
GET /mood-tracker?user_id=Raul&date=2026-05-19
```

If `date` is omitted on POST, the Lambda may default to current UTC date.

## Local testing

You can still run `main.py` directly, although it does not provide an HTTP server locally.
