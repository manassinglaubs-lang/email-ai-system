import json
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

MODEL = "openai/gpt-oss-120b"

CATEGORIES = [
    "Delivery Issue",
    "Product Complaint",
    "Refund Request",
    "Product Inquiry",
    "Technical Support",
    "General Inquiry",
]

SYSTEM_PROMPT = f"""You are an expert customer-service email analyst.
Analyze the customer email and reply with ONLY a valid JSON object using exactly these keys:

{{
  "category": one of {CATEGORIES},
  "priority": "High" | "Medium" | "Low",
  "sentiment": "Positive" | "Neutral" | "Negative",
  "key_information": {{
    "order_id": string or null,
    "product": string or null,
    "issue": string or null,
    "dates": string or null
  }},
  "recommended_action": "one short sentence for the support team",
  "response": "a polite, professional reply email"
}}

Rules:
- Priority: High = angry, urgent, or money/account access blocked. 
- Medium = problem that needs fixing but not urgent. 
- Low = simple questions.
- The response must have a greeting, show empathy when the customer is upset, give a clear next step, and end with "Customer Support Team".
- Never invent facts such as tracking numbers or refund dates.
- A delayed delivery with no other urgency is Medium, not High.
"""


def get_client(api_key: str | None = None) -> Groq:
    """Create a Groq client. The key comes from the argument or the environment."""
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        raise ValueError("GROQ_API_KEY not found. Add it to your .env file.")
    return Groq(api_key=key)

def validate(result: dict) -> dict:
    """Make sure the model's output uses only allowed values."""
    if result.get("category") not in CATEGORIES:
        result["category"] = "General Inquiry"
    if result.get("priority") not in ("High", "Medium", "Low"):
        result["priority"] = "Medium"
    if result.get("sentiment") not in ("Positive", "Neutral", "Negative"):
        result["sentiment"] = "Neutral"
    return result


def analyze_email(email_text: str, api_key: str | None = None) -> dict:
    """Send the email to Groq and return the analysis as a Python dictionary."""
    client = get_client(api_key)
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"EMAIL:\n{email_text}"},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    return validate(json.loads(completion.choices[0].message.content))


if __name__ == "__main__":
    test_email = (
        "Hello, I ordered a pair of headphones five days ago and they were "
        "supposed to arrive yesterday. I still haven't received them. "
        "Please check where my order is. Order ID: 45892."
    )
    result = analyze_email(test_email)
    print(json.dumps(result, indent=2))