// User model for FE
export default class User {
  constructor(userId, firstName, lastName, fullName, password, phone, email, roleId) {
    this.userId = userId;
    this.firstName = firstName;
    this.lastName = lastName;
    this.fullName = fullName;
    this.password = password;
    this.phone = phone;
    this.email = email;
    this.roleId = roleId;
  }
}
