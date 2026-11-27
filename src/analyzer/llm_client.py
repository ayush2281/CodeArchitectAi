
import os
from dotenv import load_dotenv
from groq import Groq

# Load the project's .env file and override older environment variables
load_dotenv(override=True)

MODEL_NAME = "qwen/qwen3.8-27b"

client = Groq(
    api_key=os.environ["GROQ_API_KEY"],
)


def generate_response(prompt: str) -> str:
    """Generate a response using the Groq-hosted Qwen model."""
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        reasoning_effort="none",
        max_tokens=300,
    )

    return response.choices[0].message.content
