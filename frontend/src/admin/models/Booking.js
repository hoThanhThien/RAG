// Booking model for FE
export default class Booking {
  constructor(bookingId, userId, tourId, bookingDate, numberOfPeople, totalAmount, status, discountId) {
    this.bookingId = bookingId;
    this.userId = userId;
    this.tourId = tourId;
    this.bookingDate = bookingDate;
    this.numberOfPeople = numberOfPeople;
    this.totalAmount = totalAmount;
    this.status = status;
    this.discountId = discountId;
  }
}
