from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://sunrise:sunrise@localhost:5432/sunrise"
    TEST_DATABASE_URL: str = "postgresql+psycopg://sunrise:sunrise@localhost:5432/sunrise_test"
    JWT_SECRET: str = "change-me-in-production"
    # 12 is passlib's default. Tests override this to 4 via the environment.
    BCRYPT_ROUNDS: int = 12

    # Empty endpoint means the local filesystem backend, so neither the tests
    # nor a bare `uvicorn` need a bucket running.
    STORAGE_ENDPOINT: str = ""
    STORAGE_ACCESS_KEY: str = ""
    STORAGE_SECRET_KEY: str = ""
    STORAGE_BUCKET: str = "sunrise-documents"
    STORAGE_LOCAL_PATH: str = "./var/documents"
    # Empty host means the console backend, so neither the tests nor a bare
    # `uvicorn` need a mail server — and nothing is ever accidentally sent to a
    # real parent from a laptop. Brevo and Resend both speak SMTP, which is why
    # there is no provider SDK here (§0.11).
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:8081"
    SCHOOL_NAME: str = "Sunrise Public School"
    ACADEMIC_YEAR: str = "2025-26"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
