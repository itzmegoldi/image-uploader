from src.repository import ImageRepository, IImageRepository


class Repo:
    def with_image_repo(self, clients):
        self.image_repo: IImageRepository = ImageRepository(clients)
        return self
