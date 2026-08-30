from src.service import IImageService, ImageService
from src.repository import IImageRepository


class Services:
    def with_image_service(self, config, clients, repo: IImageRepository):
        self.image_service: IImageService = ImageService(config, clients, repo)
        return self
