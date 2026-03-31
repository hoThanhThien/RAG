// Payment model for FE
export default class Payment {
  constructor(paymentId, bookingId, paymentDate, amount, paymentStatus, paymentMethod) {
    this.paymentId = paymentId;
    this.bookingId = bookingId;
    this.paymentDate = paymentDate;
    this.amount = amount;
    this.paymentStatus = paymentStatus;
    this.paymentMethod = paymentMethod;
  }
}
