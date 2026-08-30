import os

from src.builder import set_clients, set_config, set_services
from src.builder.clients import Clients
from src.builder.repos import Repo
from src.builder.services import Services
from src.config import Config
from src.utils import logging

logger = logging.get_logger()


def fetch_config() -> Config:
    config_path = os.path.join(os.getcwd(), "config/")
    app_env = os.environ.get("APP_ENV", "dev")
    logger.info(f"Loading file from {app_env} present at {config_path}")
    return Config.from_yaml(
        config_path,
        app_env,
    )


def build_all_clients(config) -> Clients:
    return Clients().with_s3_client(config).with_dynamodb_client(config)


def build_all_services(config, clients) -> Services:
    repo = Repo().with_image_repo(clients)
    return Services().with_image_service(config, clients, repo.image_repo)


def fetch_config_and_build_services():
    logger.info("Fetching config and building services")

    config = fetch_config()
    clients = build_all_clients(config)
    services = build_all_services(config, clients)
    set_config(config)
    set_clients(clients)
    set_services(services)

    logger.info("Fetched config and built services")
