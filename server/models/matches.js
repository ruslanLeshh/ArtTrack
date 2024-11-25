const { DataTypes } = require('sequelize');
const sequelize = require('../sequelize');
const Users = require('./users');  // Import User model
const Images = require('./images');  // Import Image model

// Define Matches model
const Matches = sequelize.define('Matches', {
  match_id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true,
  },
  similarity_score: {
    type: DataTypes.FLOAT,  // Store the similarity score as a float (e.g., 0.95)
    allowNull: false,
  },
  new_image_filename: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  matched_image_filename: {
    type: DataTypes.STRING,
    allowNull: false,
  },
},  {
    timestamps: false, // Disable createdAt and updatedAt
  });

// Associations
Matches.belongsTo(Images, {
  foreignKey: 'image_id', // The user who uploaded the matched image
});

// Matches.belongsTo(Images, {
//   foreignKey: 'matched_image_id', // The matched image (from the Images table)
// });

// Export the Matches model
module.exports = Matches;
