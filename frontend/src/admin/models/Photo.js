export default class Photo {
  constructor(photoId, tourId, caption, imageUrl, uploadDate, isPrimary) {
    this.photoId = photoId;
    this.tourId = tourId;
    this.caption = caption;
    this.imageUrl = imageUrl;
    this.uploadDate = uploadDate;
    this.isPrimary = isPrimary;
  }
}
