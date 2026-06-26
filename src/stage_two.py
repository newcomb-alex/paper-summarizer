import os
import re
import json
import argparse
from pathlib import Path
from dataclasses import dataclass
from pdf_utils import read_paper

import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-sonnet-4.6"

@dataclass
class TemplateSection:
    """A single section parsed out of the Stage 1 template."""
    name: str          # e.g. "Introduction"
    instructions: str  # the injected, section-type-specific instructions


# Parsing the Stage 1 template
# Matches blocks of the form:
#
#   ## [SECTION: Introduction]
#   <instructions>
#   ...summarizing instructions for this section...
#   </instructions>
#
SECTION_HEADER_RE = re.compile(
    r"##\s*\[SECTION:\s*(?P<name>.+?)\s*\]",
    re.IGNORECASE,
)
INSTRUCTIONS_RE = re.compile(
    r"<instructions>(?P<body>.*?)</instructions>",
    re.IGNORECASE | re.DOTALL,
)


def parse_template(template_text: str) -> list[TemplateSection]:
    """
    Split the Stage 1 template into individual sections.

    Each section is delimited by a `## [SECTION: <name>]` header, and its
    instructions are wrapped in `<instructions>...</instructions>` tags.
    """
    sections: list[TemplateSection] = []

    # Find all section header positions so we can slice between them.
    headers = list(SECTION_HEADER_RE.finditer(template_text))
    if not headers:
        raise ValueError(
            "No `## [SECTION: ...]` markers found in the template. "
            "Check that Stage 1 produced the expected format."
        )

    for i, header in enumerate(headers):
        name = header.group("name").strip()

        # The block for this section runs to the next header (or EOF).
        start = header.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(template_text)
        block = template_text[start:end]

        instr_match = INSTRUCTIONS_RE.search(block)
        if instr_match:
            instructions = instr_match.group("body").strip()
        else:
            # Fall back to the raw block if tags are missing.
            instructions = block.strip()

        sections.append(TemplateSection(name=name, instructions=instructions))

    return sections


def summarize_section(
    paper_text: str,
    section: TemplateSection,
    system_prompt: str = "",
    model: str = MODEL,
    temperature: float = 0.3,
    max_tokens: int = 4000,
    timeout: int = 120,
) -> str:
    """
    Stage 2 (per section).

    Given the full paper and a single section's instructions, ask the LLM to
    write the summary for that section only. Each call is an independent
    session, so no conversation state carries over between sections.

    The system prompt is left empty by default for you to populate.
    """
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY not found. Add it to your .env file."
        )

    user_prompt = (
        "You are summarizing one section of the paper below.\n\n"
        f"Section to summarize: {section.name}\n\n"
        "Follow these section-specific instructions exactly:\n"
        "<instructions>\n"
        f"{section.instructions}\n"
        "</instructions>\n\n"
        "Here is the full paper for reference:\n"
        "<paper>\n"
        f"{paper_text}\n"
        "</paper>\n\n"
        f"Write only the summary content for the '{section.name}' section. "
        "Do not include the section heading; it will be added automatically."
    )

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
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
    if "error" in data:
        raise RuntimeError(f"OpenRouter API error: {data['error']}")

    return data["choices"][0]["message"]["content"].strip()


def summarize_paper(
    paper_text: str,
    template_text: str,
    system_prompt: str = "",
    title: str = "Paper Summary",
    model: str = MODEL,
    temperature: float = 0.3,
    max_tokens: int = 4000,
) -> str:
    """
    Run Stage 2 end-to-end:
      1. Parse the template into sections.
      2. Summarize each section in its own fresh session.
      3. Assemble everything into one markdown document.
    """
    sections = parse_template(template_text)

    parts: list[str] = [f"# {title}\n"]

    for idx, section in enumerate(sections, start=1):
        print(f"[{idx}/{len(sections)}] Summarizing section: {section.name} ...")
        body = summarize_section(
            paper_text=paper_text,
            section=section,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        parts.append(f"## {section.name}\n\n{body}\n")

    return "\n".join(parts)

def read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")

def write_text(text: str, path: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Stage 2 of Paper-Summarizer: fill in the template, "
                    "one section per session, and assemble the summary."
    )
    parser.add_argument("paper", help="Path to the input paper (.txt or .md).")
    parser.add_argument("template", help="Path to the Stage 1 template (.md).")
    parser.add_argument(
        "-o", "--output", default="summary.md",
        help="Path to write the final summary (default: summary.md).",
    )
    parser.add_argument(
        "-s", "--system-prompt-file", default=None,
        help="Optional path to a file containing the system prompt.",
    )
    parser.add_argument(
        "-t", "--title", default="Paper Summary",
        help="Title for the summary document.",
    )
    parser.add_argument(
        "--temperature", type=float, default=0.3,
        help="Sampling temperature (default: 0.3).",
    )
    parser.add_argument(
        "--max-tokens", type=int, default=4000,
        help="Max tokens per section (default: 4000).",
    )
    args = parser.parse_args()

    paper_text = read_paper(args.paper)        # PDF-aware
    template_text = read_text(args.template)   # template is ALWAYS .md — keep text reader

    system_prompt = ""
    if args.system_prompt_file:
        system_prompt = read_text(args.system_prompt_file)

    summary = summarize_paper(
        paper_text=paper_text,
        template_text=template_text,
        system_prompt=system_prompt,
        title=args.title,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )

    write_text(summary, args.output)
    print(f"\nSummary written to: {args.output}")


if __name__ == "__main__":
    main()