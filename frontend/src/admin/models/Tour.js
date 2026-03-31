// Tour model for FE
export default class Tour {
  constructor(tourId, title, location, description, capacity, price, startDate, endDate, status, categoryId) {
    this.tourId = tourId;
    this.title = title;
    this.location = location;
    this.description = description;
    this.capacity = capacity;
    this.price = price;
    this.startDate = startDate;
    this.endDate = endDate;
    this.status = status;
    this.categoryId = categoryId;
  }
}
