"""AI API adapter for Calora.

io_manager supplies input records. This module sends every record through the
AI API and returns validated data for logic_manager to format. Domain rules,
calculations, filtering, and display formatting belong elsewhere.
"""

import json
import logging
import os
from typing import Any, Callable, Iterable
from urllib import error, request
from urllib.parse import quote, urlencode, urlsplit, urlunsplit

try:
    from config import GEMINI_API_KEY as LOCAL_GEMINI_API_KEY
except ImportError:
    LOCAL_GEMINI_API_KEY = ""


LOGGER = logging.getLogger(__name__)
DEFAULT_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-2.5-flash-lite"
REQUIRED_MEAL_FIELDS = {
    "slot", "name", "source", "calories", "protein_g",
    "carbohydrates_g", "fat_g", "cost", "ingredients",
}
REQUIRED_SLOTS = {"breakfast", "lunch", "dinner"}


def build_prompt(input_record: dict[str, Any]) -> str:
    """Build the AI prompt from one input record without interpreting it."""
    return f"""You are Calora's meal recommendation engine.
Use the user's input record below to generate a full-day meal plan.
Return JSON only. Do not include markdown, comments, or explanatory text.
Return an object with a 'meals' list containing breakfast, lunch, and dinner.
Each meal must contain: slot, name, source, calories, protein_g,
carbohydrates_g, fat_g, cost, and ingredients.

User input record:
{json.dumps(input_record, ensure_ascii=True, default=str)}"""


def make_api_payload(prompt: str, model: str = DEFAULT_MODEL) -> bytes:
    """Create a Gemini generateContent request body."""
    return json.dumps({
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }).encode("utf-8")


def call_api(prompt: str, api_key: str, model: str = DEFAULT_MODEL,
             endpoint: str = DEFAULT_ENDPOINT,
             transport: Callable[[str, dict[str, str], bytes], str] | None = None) -> str:
    """Call Gemini and return its raw response text."""
    endpoint = endpoint.format(model=quote(model, safe=""))
    parts = urlsplit(endpoint)
    query = dict(part.split("=", 1) for part in parts.query.split("&") if "=" in part)
    query["key"] = api_key
    endpoint = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
    headers = {"Content-Type": "application/json"}
    body = make_api_payload(prompt, model)
    if transport:
        return transport(endpoint, headers, body)

    api_request = request.Request(endpoint, data=body, headers=headers, method="POST")
    with request.urlopen(api_request, timeout=60) as response:
        return response.read().decode("utf-8")


def extract_content(raw_api_response: str | dict[str, Any]) -> Any:
    """Extract generated text from a Gemini response."""
    response = json.loads(raw_api_response) if isinstance(raw_api_response, str) else raw_api_response
    return response["candidates"][0]["content"]["parts"][0]["text"]


def parse_response(raw_api_response: str | dict[str, Any]) -> dict[str, Any]:
    """Parse the provider envelope and the model's JSON content."""
    content = extract_content(raw_api_response)
    parsed = json.loads(content) if isinstance(content, str) else content
    if not isinstance(parsed, dict):
        raise ValueError("AI content must be a JSON object")
    return parsed


def validate_response(response_data: dict[str, Any]) -> None:
    """Validate only the API response contract; formatting remains elsewhere."""
    meals = response_data.get("meals")
    if not isinstance(meals, list) or not meals:
        raise ValueError("Response must contain a non-empty meals list")

    slots = set()
    for meal in meals:
        if not isinstance(meal, dict):
            raise ValueError("Every meal must be an object")
        missing = REQUIRED_MEAL_FIELDS - set(meal)
        if missing:
            raise ValueError("Meal is missing fields: " + ", ".join(sorted(missing)))
        if not isinstance(meal["ingredients"], list):
            raise ValueError("Meal ingredients must be a list")
        slots.add(meal["slot"])
    if not REQUIRED_SLOTS.issubset(slots):
        raise ValueError("Response must include breakfast, lunch, and dinner")


def error_result(input_record: dict[str, Any], message: str) -> dict[str, Any]:
    """Return a safe failure record for downstream processing."""
    return {
        "success": False,
        "input_record": input_record,
        "error": message,
        "meals": [],
    }


def process_record(input_record: dict[str, Any], api_key: str | None = None,
                   model: str = DEFAULT_MODEL, endpoint: str = DEFAULT_ENDPOINT,
                   retries: int = 2,
                   transport: Callable[[str, dict[str, str], bytes], str] | None = None) -> dict[str, Any]:
    """Send one record through the API and return data or a logged failure."""
    key = api_key or os.getenv("GEMINI_API_KEY") or LOCAL_GEMINI_API_KEY
    if not key:
        message = "GEMINI_API_KEY is not configured"
        LOGGER.error(message)
        return error_result(input_record, message)

    prompt = build_prompt(input_record)
    attempts = max(1, retries + 1)
    last_error = "Unknown AI error"
    for attempt in range(1, attempts + 1):
        try:
            raw_response = call_api(prompt, key, model, endpoint, transport)
            response_data = parse_response(raw_response)
            validate_response(response_data)
            return {"success": True, "input_record": input_record, "data": response_data}
        except (error.URLError, TimeoutError, OSError, KeyError, IndexError,
                TypeError, ValueError, json.JSONDecodeError) as exc:
            last_error = str(exc)
            LOGGER.warning("AI record attempt %s/%s failed: %s", attempt, attempts, last_error)

    LOGGER.error("AI record failed after %s attempts: %s", attempts, last_error)
    return error_result(input_record, last_error)


def process_records(input_records: Iterable[dict[str, Any]], **settings) -> list[dict[str, Any]]:
    """Process every input record, continuing when an individual record fails."""
    return [process_record(record, **settings) for record in input_records]


# LINKING SECTION
# io_manager can call process_record for one input or process_records for many.
# logic_manager should receive each result and handle formatting and display tags.
