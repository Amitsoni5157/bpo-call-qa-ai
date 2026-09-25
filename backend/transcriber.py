import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found")

client = Groq(api_key=api_key)

def transcribe_audio(file_path: str) -> str:
    """
    Audio file (.mp3 / .wav) ko text transcript me convert karta hai
    Whisper-large-v3 model use karke.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file nahi mili: {file_path}")

    with open(file_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(file_path), file.read()),
            model="whisper-large-v3",
            response_format="text",
            temperature=0.0, # Factual transcription ke liye randomness zero,
            prompt="A clear customer support conversation between an agent and a client discussing orders, quantities, pricing, verification, delivery, and service issues."
        )

    return transcription.strip()