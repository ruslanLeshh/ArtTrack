const { DataTypes } = require('sequelize');
const sequelize = require('../sequelize');
const Users = require('./users');  // Import User model

const Images = sequelize.define('Images', {
  image_id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true,
  },
  file_path: {
    type: DataTypes.STRING,
    allowNull: false,
  },
});

Images.belongsTo(Users, {
  foreignKey: 'user_id', // Linking Image to User
});

module.exports = Images;
