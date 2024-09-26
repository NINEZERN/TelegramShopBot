# Translate db data to class
class Product:
    def __init__(self, id: int, caption: str, description: str, price: float, media_type, media_id, category):
        self.id = id
        self.caption = caption
        self.description = description
        self.price = price
        self.media_type = media_type
        self.media_id = media_id
        self.category = category