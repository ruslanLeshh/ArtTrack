const { DataTypes } = require('sequelize');
const sequelize = require('../sequelize');
const Users = require('./users');  // Import User model

const Images = sequelize.define('Images', {
  image_id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true,
  },
  filename: {
    type: DataTypes.STRING,
    allowNull: false,
  },
},   {
  timestamps: false, // Disable createdAt and updatedAt
});

Images.belongsTo(Users, {
  foreignKey: 'user_id', // Linking Image to User
});

module.exports = Images;
