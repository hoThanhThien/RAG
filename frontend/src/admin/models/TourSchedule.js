export default class TourSchedule {
  constructor(scheduleId, tourId, dayNumber, time, location, activity) {
    this.scheduleId = scheduleId;
    this.tourId = tourId;
    this.dayNumber = dayNumber;
    this.time = time;
    this.location = location;
    this.activity = activity;
  }
}
