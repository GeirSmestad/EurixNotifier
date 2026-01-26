from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """Read the HTML below and determine the following: 

1) What dates and editions for this event are available for registration? 
2) What *future* dates and editions does the page inform about?

It is {current_date} today.

The page describes which editions of the festival are currently open for registration, as well as information about previous festivals. (We are not interested in the previous festivals, and we are also not interested in any *2026* festival).

You are responsible for deciding whether to notify the user about festival availability. Notify if this web page has information about any *2027* edition of this festival. It is normally arranged in spring and autumn.

The user will want to know if *information is available* for a 2027 festival, and also if *registration has been opened* for a 2027 festival.

Regardless of whether you notify or not, you must compose a brief SMS explaining the current situation to the user. Lead with the status regarding any 2027 edition of the festival (whether it is mentioned yet or not). The SMS must be in English and use only symbols from the GSM-7 alphabet.

Return only JSON, as per the following example:

{{
    "sms_content": "Insert your SMS content here",
    "should_notify": true
}}

Here is the HTML that you will analyze:

{html}
"""

SMS_PREFIX = "Eurix-bot sier:\n\n"
SMS_SUFFIX = (
    "\n\nSi ifra til Geir hvis du ikke vil motta disse meldingene! :)"
)


@dataclass(frozen=True)
class AnalysisResult:
    sms_content: str  # full final SMS, including prefix/suffix
    should_notify: bool


def _wrap_sms(content: str) -> str:
    content = (content or "").strip()
    if not content:
        content = "Ingen informasjon tilgjengelig (tomt svar fra analyse)."
    return f"{SMS_PREFIX}{content}{SMS_SUFFIX}"


def _extract_json_object(raw: str) -> dict:
    try:
        return json.loads(raw)
    except Exception:
        # Try to salvage when the model wraps JSON in text.
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(raw[start : end + 1])


def _call_openai_text(*, api_key: str, model: str, prompt: str) -> str:
    # Prefer OpenAI's newer SDK interface, but keep a pragmatic fallback.
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    # Attempt Responses API first (newer), then fall back to Chat Completions.
    try:
        responses = getattr(client, "responses", None)
        if responses is not None:
            resp = responses.create(
                model=model,
                input=[{"role": "user", "content": prompt}],
            )
            out_text = getattr(resp, "output_text", None)
            if isinstance(out_text, str) and out_text.strip():
                return out_text
    except Exception:
        pass

    chat = getattr(client, "chat", None)
    if chat is None:
        raise RuntimeError("OpenAI client does not support chat or responses APIs.")

    # response_format is supported by many models; if rejected by the API, we still parse.
    resp = chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content or ""


def analyze_html_for_sms(*, html: str, today: date, model: str, api_key: str) -> AnalysisResult:
    prompt = PROMPT_TEMPLATE.format(current_date=today.isoformat(), html=html)

    raw: str | None = None
    try:
        raw = _call_openai_text(api_key=api_key, model=model, prompt=prompt)
        obj = _extract_json_object(raw)
        sms_content = obj.get("sms_content", "")
        should_notify = obj.get("should_notify", False)
        if not isinstance(sms_content, str):
            raise ValueError("sms_content was not a string")
        if not isinstance(should_notify, bool):
            raise ValueError("should_notify was not a bool")
        return AnalysisResult(sms_content=_wrap_sms(sms_content), should_notify=should_notify)
    except Exception as e:
        # Log full exception for debugging (will show in cron log via stderr redirection).
        if raw:
            logger.error("OpenAI raw response (truncated): %s", raw[:2000])
        logger.exception("OpenAI analysis failed: %s", e)

        # Fallback that still logs a useful message in Norwegian.
        fallback = (
            "Jeg klarte ikke å tolke nettsiden automatisk denne gangen, så jeg kan ikke si sikkert om Eurix 2027 er annonsert "
            "eller om påmelding er åpnet. Be Geir om å kikke på loggen."
        )
        return AnalysisResult(sms_content=_wrap_sms(fallback), should_notify=False)

