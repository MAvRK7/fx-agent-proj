from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # ────────────────────────────────────────
    # LLM providers & models
    # ────────────────────────────────────────
    OPENROUTER_API_KEY: str
    MISTRAL_API_KEY: str

    MODEL_PRIMARY: str = "stepfun/step-3.5-flash:free"
    MODEL_FALLBACK: str = "mistral-small-latest"

    # later add temperature, max_tokens, etc. per model
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int | None = None

    # Agent behavior
    MAX_TOOL_STEPS: int = 8

    # Cache
    CACHE_TTL_HOURS: int = 6

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )


settings = Settings()