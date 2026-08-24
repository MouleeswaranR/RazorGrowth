from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Loads and validates application configuration settings from environment variables."""

    app_name: str = Field(default="RazorGrowth AI", description="Application service name")
    environment: str = Field(default="development", description="Deployment environment")
    debug: bool = Field(default=True, description="Debug mode toggle")

    # Database Configuration
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/razorgrowth",
        description="Async PostgreSQL connection string"
    )

    # Razorpay API Credentials (Test Mode)
    razorpay_key_id: str = Field(default="", description="Razorpay Test Key ID")
    razorpay_key_secret: str = Field(default="", description="Razorpay Test Key Secret")
    razorpay_webhook_secret: str = Field(default="", description="Razorpay Webhook Secret")

    # AI / LLM Multi-Provider Configurations
    # Model tiers are benchmarked against the real 6-tool schema (see bench_models.py).
    # Each provider tries tier 1, then 2, then 3 before the chain moves to the next provider.
    # 1. NVIDIA NIM (Primary for Agentic Tool-Calling)
    nvidia_nim_api_key: str = Field(default="", description="NVIDIA NIM API Key")
    nvidia_nim_base_url: str = Field(default="https://integrate.api.nvidia.com/v1", description="NVIDIA NIM Base URL")
    nvidia_nim_model: str = Field(default="nvidia/nemotron-3-super-120b-a12b", description="NVIDIA NIM tier-1 model (100% tool accuracy @ 2.2s)")
    nvidia_nim_model_fallback_2: str = Field(default="nvidia/llama-3.3-nemotron-super-49b-v1.5", description="NVIDIA NIM tier-2 model (100% accuracy, slower @ 24.6s)")
    nvidia_nim_model_fallback_3: str = Field(default="nvidia/nemotron-3.5-lightning-30b-a3b", description="NVIDIA NIM tier-3 model (78% accuracy @ 4.8s)")

    # 2. OpenRouter (Secondary Backup for Agentic Decisions & Chat)
    openrouter_api_key: str = Field(default="", description="OpenRouter API Key")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", description="OpenRouter Base URL")
    ai_model_name: str = Field(default="nvidia/nemotron-3-super-120b-a12b:free", description="OpenRouter default model ID")
    agentic_model_name: str = Field(default="nvidia/nemotron-3-super-120b-a12b:free", description="OpenRouter tier-1 model (100% tool accuracy @ 2.1s)")
    openrouter_model_fallback_2: str = Field(default="nvidia/nemotron-3-ultra-550b-a55b:free", description="OpenRouter tier-2 model (89% accuracy @ 3.9s)")
    openrouter_model_fallback_3: str = Field(default="liquid/lfm-2.5-2.6b:free", description="OpenRouter tier-3 model (67% accuracy @ 1.3s, different vendor for outage diversity)")

    # 3. Groq (Primary for Ultra-Fast Real-Time Streaming Narration)
    groq_api_key: str = Field(default="", description="Groq API Key for fast SSE streaming")
    groq_base_url: str = Field(default="https://api.groq.com/openai/v1", description="Groq Base URL")
    groq_model: str = Field(default="llama-3.3-70b-versatile", description="Groq streaming model identifier")

    # 4. Mistral AI (Tertiary Provider Option)
    mistral_api_key: str = Field(default="", description="Mistral AI API Key")
    mistral_base_url: str = Field(default="https://api.mistral.ai/v1", description="Mistral Base URL")
    mistral_model: str = Field(default="mistral-small-latest", description="Mistral model identifier")

    openai_api_key: str = Field(default="", description="OpenAI generic fallback key")
    enable_agentic_mode: bool = Field(default=True, description="Feature flag for agentic scan loop")
    agentic_max_steps: int = Field(default=9, description="Max tool iterations in agentic loop (6 diagnostic tools plus headroom for model-chosen revisits)")
    embedding_model_name: str = Field(default="all-MiniLM-L6-v2", description="Embedding model identifier")


    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


settings = Settings()

