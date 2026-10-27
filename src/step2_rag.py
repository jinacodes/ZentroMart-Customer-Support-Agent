import os
import re
from pathlib import Path
from collections import Counter

from google import genai
from google.genai import types


# Find the project folder, regardless of where Python is launched.
ROOT = Path(__file__).resolve().parent.parent
KB_DIR = ROOT / "kb"

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"],
    http_options=types.HttpOptions(timeout=30000),
)


# Higher-priority sources win when documents disagree.
SOURCE_PRIORITY = {
    "policy": 5,
    "agent_guide": 4,
    "help": 3,
    "faq": 2,
    "marketing": 1,
    "meta": 4,
}


def read_documents():
    """Load current documents and split them into searchable sections."""
    sections = []

    for path in KB_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")

        # Read metadata from the document header.
        header_match = re.match(
            r"\A---\s*\n(.*?)\n---\s*(?:\n|$)",
            text,
            re.S,
        )

        if not header_match:
            continue

        header = {}
        for line in header_match.group(1).splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                header[key.strip()] = value.strip().strip('"').strip("'")

        # Never use a superseded document as current policy.
        if header.get("status", "").lower() == "superseded":
            continue

        # Split the document at each section heading.
        parts = re.split(r"(?m)^## ", text)

        for part in parts[1:]:
            lines = part.strip().splitlines()

            if not lines:
                continue

            heading = lines[0].strip()
            body = "\n".join(lines[1:]).strip()

            if not body:
                continue

            sections.append({
                "file": path.name,
                "doc_id": header.get("doc_id", path.stem),
                "title": header.get("title", path.stem),
                "doc_type": header.get("doc_type", "unknown"),
                "section": heading,
                "text": body,
            })

    return sections


def tokenize(text):
    """Convert text to simple searchable words."""
    return re.findall(r"[a-z0-9]+", text.lower())


def retrieve(question, sections, top_k=4):
    """Rank sections using word overlap and source authority."""
    query_words = set(tokenize(question))

    # Ignore common words that aren't useful for searching.
    stop_words = {
        "the", "a", "an", "is", "are", "i", "my",
        "do", "does", "what", "how", "can", "to",
        "for", "of", "and", "in", "on", "it", "you",
        "we", "me", "please", "tell",
    }

    useful_words = query_words - stop_words

    scored = []

    for section in sections:
        section_words = tokenize(
            section["title"] + " " +
            section["section"] + " " +
            section["text"]
        )

        counts = Counter(section_words)

        overlap = sum(
            1 for word in useful_words if counts[word] > 0
        )

        if overlap == 0 and section["doc_id"] != "POL-DWM":
            continue

        # Small boost for words in the section heading and title.
        heading_words = set(tokenize(
            section["title"] + " " + section["section"]
        ))

        heading_matches = len(useful_words & heading_words)
        priority = SOURCE_PRIORITY.get(section["doc_type"], 0)

        score = overlap + (heading_matches * 0.5) + (priority * 0.15)

        # Boost damaged, wrong, or missing item policy sections.
        issue_words = {
            "damaged", "damage", "defective", "expired",
            "wrong", "missing", "incorrect", "received",
            "instead", "different", "colour", "color",
            "mismatch", "mismatched",
        }

        if (
            useful_words & issue_words
            and section["doc_id"] == "POL-DWM"
        ):
            score += 3

        scored.append((score, section))

    scored.sort(key=lambda item: item[0], reverse=True)

    return [section for score, section in scored[:max(top_k, 6)]]


def ask_with_rag(question):
    """Retrieve evidence, then ask Gemini to answer from that evidence."""
    sections = read_documents()
    matches = retrieve(question, sections)


    if not matches:
        return (
            "I couldn't find relevant information in the current "
            "company documents.",
            [],
        )

    evidence = "\n\n".join(
        f"Source: {section['file']} | "
        f"{section['doc_id']} | {section['section']}\n"
        f"{section['text']}"
        for section in matches
    )

    prompt = f"""
You are ZentroMart's AI customer support assistant.

For a new conversation, make it clear that you are an AI assistant.
Answer the customer's question using the evidence below.
Treat current policy documents as more authoritative than FAQs,
help articles, or marketing pages.
Do not invent company policies, promises, fees, or deadlines.
If the evidence does not answer the question, say:
"I don't know based on the company documents."
If sources conflict, follow the higher-priority source.
Give a direct, actionable answer to the customer's question.
When a policy explains what the customer should do, summarise
the relevant steps, deadlines, required evidence, and available
resolutions from that policy.
Do not merely name or refer to a policy without explaining
what it means for the customer.
Use simple language and avoid irrelevant policy details.

EVIDENCE:
{evidence}

CUSTOMER QUESTION:
{question}
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
    )

    answer = response.text or (
        "I couldn't generate a response just now. Please try again."
    )

    return answer, matches


def test_retrieval_only():
    """Check which knowledge-base sections are retrieved."""
    sections = read_documents()

    test_questions = [
        "How fast are refunds to the ZentroMart Wallet?",
        "Can I schedule a delivery at midnight?",
        "What is the return window for clothing items?",
    ]

    for question in test_questions:
        print(f"\nQuestion: {question}")
        matches = retrieve(question, sections)

        if not matches:
            print("No relevant sections found.")
            continue

        for section in matches:
            print(
                f"- {section['file']} | "
                f"{section['section']}"
            )


if __name__ == "__main__":
    print("ZentroMart AI Support — Step 2 RAG")
    print("Type 'exit' to quit.\n")

    while True:
        question = input("Your question: ").strip()

        if question.lower() in {"exit", "quit"}:
            print("See you!")
            break

        if not question:
            continue

        try:
            answer, sources = ask_with_rag(question)

            print("\nAgent reply:")
            print(answer)

            print("\nEvidence used:")

            if sources:
                for source in sources:
                    print(
                        f"- {source['file']} | "
                        f"{source['doc_id']} | "
                        f"{source['section']}"
                    )
            else:
                print("- No relevant sections found.")

            print()

        except Exception as error:
            print(f"\nRequest failed: {error}")
            print("You can try another question.\n")
