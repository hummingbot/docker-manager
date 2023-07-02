from typing import Optional

from pydantic import BaseSettings

class DockerSettings(BaseSettings):
    class Config:
        env_file = f".env"

    docker_host:Optional[str] = None
    docker_cert_path:Optional[str] = None
    docker_tls_verify:Optional[str] = None