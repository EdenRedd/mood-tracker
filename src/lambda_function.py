import logging

from main import lambda_handler

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# AWS Lambda entrypoint: lambda_function.lambda_handler
# This forwards the request to main.lambda_handler.

__all__ = ["lambda_handler"]
