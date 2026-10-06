import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2:3b",
)

OLLAMA_API_BASE = os.getenv(
    "OLLAMA_API_BASE",
    "http://localhost:11434",
)

CHEAP_MODEL = os.getenv(
    "CHEAP_MODEL",
    "nvidia/nemotron-3.5-lightning-30b-a3b",
)

STRONG_MODEL = os.getenv(
    "STRONG_MODEL",
    "nvidia/nemotron-3-ultra-550b-a55b",
)

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

NVIDIA_API_BASE = os.getenv(
    "NVIDIA_API_BASE",
    "https://integrate.api.nvidia.com/v1",
)

PROVIDER_TIMEOUT_SECONDS = float(
    os.getenv("PROVIDER_TIMEOUT_SECONDS", "8")
)