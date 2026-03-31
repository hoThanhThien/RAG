export default class Discount {
  constructor(discountId, code, description, discountAmount, isPercent, startDate, endDate) {
    this.discountId = discountId;
    this.code = code;
    this.description = description;
    this.discountAmount = discountAmount;
    this.isPercent = isPercent;
    this.startDate = startDate;
    this.endDate = endDate;
  }
}
