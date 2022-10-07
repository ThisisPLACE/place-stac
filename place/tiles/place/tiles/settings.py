from titiler.application.settings import ApiSettings

class Settings(ApiSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True