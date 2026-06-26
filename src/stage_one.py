import os
import json
import argparse
from pathlib import Path
from pdf_utils import read_paper

import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-sonnet-4.6"


def build_template(
    paper_text: str,
    system_prompt: str = "",
    model: str = MODEL,
    max_tokens: int = 8000,
    timeout: int = 120,
) -> str:
    """
    Stage 1 of the Paper-Summarizer.

    Prompts an LLM to parse an input paper, extract its main headings, and
    inject section-type-specific summarizing instructions, producing a
    summary *template* unique to this paper.

    Parameters
    ----------
    paper_text : str
        The full text of the paper to be parsed.
    system_prompt : str
        The system prompt. Intentionally left empty by default so you can
        populate it yourself with the section-type-dependent instructions
        that should be injected into the template.
    model : str
        OpenRouter model identifier.
    max_tokens : int
        Maximum tokens to generate for the template.
    timeout : int
        Request timeout in seconds.

    Returns
    -------
    str
        The generated summary template (markdown).
    """
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY not found. Add it to your .env file."
        )

    # The user message carries the paper itself. The instructions on *how*
    # to build the template (and the section-type-specific injection rules)
    # live in the system prompt, which you will populate.
    user_prompt = (
        "Here is the paper to parse. Extract its main headings and produce "
        "the summary template as instructed.\n\n"
        "<paper>\n"
        f"{paper_text}\n"
        "</paper>"
    )

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        OPENROUTER_URL,
        headers=headers,
        data=json.dumps(payload),
        timeout=timeout,
    )
    response.raise_for_status()

    data = response.json()

    # Defensive check: surface API-level errors that return HTTP 200.
    if "error" in data:
        raise RuntimeError(f"OpenRouter API error: {data['error']}")

    template = data["choices"][0]["message"]["content"]
    return template


def write_template(template: str, path: str) -> None:
    """Write the generated template to disk for review."""
    Path(path).write_text(template, encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(
        description="Stage 1 of Paper-Summarizer: build a per-paper "
                    "summary template."
    )
    parser.add_argument(
        "paper",
        help="Path to the input paper (.txt or .md).",
    )
    parser.add_argument(
        "-o", "--output",
        default="template.md",
        help="Path to write the generated template (default: template.md).",
    )
    parser.add_argument(
        "-s", "--system-prompt-file",
        default=None,
        help="Optional path to a file containing the system prompt. "
             "If omitted, the system prompt is left empty.",
    )
    parser.add_argument(
        "--max-tokens", type=int, default=8000,
        help="Max tokens for the generated template (default: 8000).",
    )
    args = parser.parse_args()

    paper_text = read_paper(args.paper)

    system_prompt = ""
    if args.system_prompt_file:
        system_prompt = Path(args.system_prompt_file).read_text(
            encoding="utf-8"
        )

    template = build_template(
        paper_text=paper_text,
        system_prompt=system_prompt,
        max_tokens=args.max_tokens,
    )

    write_template(template, args.output)

    print(f"Template written to: {args.output}\n")
    print("----- TEMPLATE PREVIEW -----\n")
    print(template)


if __name__ == "__main__":
    main()