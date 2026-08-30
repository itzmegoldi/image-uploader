from typing import Optional

from src.builder.clients import Clients
from src.builder.services import Services
from src.config import Config

__svc: Optional[Services] = None
__cfg: Optional[Config] = None
__clients: Optional[Clients] = None


def get_config() -> Config:
    if __cfg is None:
        raise ValueError
    return __cfg


def get_services() -> Services:
    if __svc is None:
        raise ValueError
    return __svc


def set_config(config: Config):
    global __cfg  # pylint: disable=global-statement
    __cfg = config


def set_services(service: Services):
    global __svc  # pylint: disable=global-statement
    __svc = service


def get_clients() -> Clients:
    if __clients is None:
        raise ValueError
    return __clients


def set_clients(cl: Clients):
    global __clients  # pylint: disable=global-statement
    __clients = cl
