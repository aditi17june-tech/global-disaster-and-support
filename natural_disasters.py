"""Fetch active natural-event reports and summarize them with the OpenAI API."""

import json
import os
from getpass import getpass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

EONET_URL = "https://eonet.gsfc.nasa.gov/api/v3/events?status=open&limit=50"
OPENAI_URL = "https://api.openai.com/v1/responses"
MODEL = "gpt-5-mini"


def request_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make an HTTP request and decode its JSON response."""
    request_headers = {"Accept": "application/json"}
    if headers:
        request_headers.update(headers)

    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    if body is not None:
        request_headers["Content-Type"] = "application/json"

    request = Request(url, data=body, headers=request_headers)
    try:
        with urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {error.code} from {url}: {details}") from error
    except URLError as error:
        raise RuntimeError(f"Could not reach {url}: {error.reason}") from error
    except json.JSONDecodeError as error:
        raise RuntimeError(f"The response from {url} was not valid JSON.") from error

    if not isinstance(result, dict):
        raise RuntimeError(f"Expected a JSON object from {url}.")
    return result


def get_active_events() -> list[dict[str, Any]]:
    """Return active events from NASA's EONET API."""
    result = request_json(EONET_URL)
    events = result.get("events")
    if not isinstance(events, list):
        raise RuntimeError("NASA EONET response did not contain an events list.")
    return [event for event in events if isinstance(event, dict)]


def prepare_event_records(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep useful event facts and their source links for the model."""
    records = []
    for event in events:
        geometries = event.get("geometry") or []
        latest = max(
            (item for item in geometries if isinstance(item, dict)),
            key=lambda item: item.get("date", ""),
            default={},
        )
        coordinates = latest.get("coordinates")

        records.append(
            {
                "event": event.get("title", "Untitled event"),
                "categories": [
                    category.get("title")
                    for category in event.get("categories", [])
                    if isinstance(category, dict) and category.get("title")
                ],
                "latest_reported_date": latest.get("date"),
                "coordinates": coordinates,
                "magnitude": latest.get("magnitudeValue"),
                "magnitude_unit": latest.get("magnitudeUnit"),
                "source": event.get("link"),
            }
        )
    return records


def summarize_events(
    records: list[dict[str, Any]], api_key: str
) -> str:
    """Ask the OpenAI Responses API to summarize the supplied event records."""
    payload = {
        "model": MODEL,
        "instructions": (
            "Summarize these NASA EONET natural-event reports for a general "
            "audience. Use only facts present in the supplied records; do not "
            "guess impacts, casualties, or locations. State that reports may "
            "change, and include the source link for each event you mention."
        ),
        "input": json.dumps(records, ensure_ascii=False),
    }
    result = request_json(
        OPENAI_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        payload=payload,
    )

    text = "\n".join(
        part["text"]
        for item in result.get("output", [])
        if item.get("type") == "message"
        for part in item.get("content", [])
        if part.get("type") == "output_text" and isinstance(part.get("text"), str)
    )
    if not text.strip():
        raise RuntimeError("The OpenAI API response did not contain summary text.")
    return text


def main() -> None:
    """Fetch current reports and print a sourced summary."""
    api_key = os.environ.get("OPENAI_API_KEY") or getpass(
        "OpenAI API key (input hidden): "
    ).strip()
    if not api_key:
        raise ValueError("An OpenAI API key is required.")

    events = get_active_events()
    if not events:
        print("NASA EONET currently returned no active events.")
        return

    records = prepare_event_records(events)
    print(f"NASA EONET returned {len(records)} active event reports.")
    print(summarize_events(records, api_key))
    print("\nThis is an informational summary, not an emergency alert.")
    print("For safety decisions, consult local authorities and official agencies.")


if __name__ == "__main__":
    main()
