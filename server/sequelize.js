const { Sequelize } = require('sequelize');

// Initialize Sequelize with PostgreSQL connection details
const sequelize = new Sequelize('postgres://postgres:pg13@localhost:5432/postgres', {
  dialect: 'postgres',
  logging: false,  // Disable logging (optional)
});
 
module.exports = sequelize;
