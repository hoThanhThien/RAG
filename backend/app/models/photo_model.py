class Photo:
    def __init__(self, photo_id: int, tour_id: int, caption: str, image_url: str, upload_date: str, is_primary: bool):
        self.photo_id = photo_id
        self.tour_id = tour_id
        self.caption = caption
        self.image_url = image_url
        self.upload_date = upload_date
        self.is_primary = is_primary
