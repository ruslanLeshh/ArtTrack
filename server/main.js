const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const bcrypt = require('bcrypt');
const { Pool } = require('pg');

const sequelize = require('./sequelize');
const Users = require('./models/users');
const Images = require('./models/images');

const multer = require('multer'); // For handling file uploads
const path = require('path');
const fs = require('fs');

// Initialize express app
const app = express();
app.use(bodyParser.json());
app.use(cors());
app.use('/images', express.static(path.join(__dirname, 'images')));
// Connect to PostgreSQL pool
const pool = new Pool({
    user: 'postgres',
    host: 'localhost',
    database: 'postgres',
    password: 'pg13',
    port: 5432,
});

// test connection
pool
    .connect()
    .then(() => {
        console.log('Connected to PostgreSQL database');
    })
    .catch((err) => {
        console.error('Error connecting to PostgreSQL database', err);
    });

// Sync Sequelize models with PostgreSQL database (create tables if they don't exist)
async function setupDatabase() {
    try {
        await sequelize.sync({ force: false });  // don't drop tables, just sync
        console.log('Database synced successfully!');
    } catch (error) {
        console.error('Error syncing database:', error);
    }
}

setupDatabase();

// Login and account creation route
app.post('/login', async (req, res) => {
    const { username, password } = req.body;
    try {
        // Check if the user exists in the database using Sequelize
        const user = await Users.findOne({ where: { username } });

        if (!user) {
            // If user doesn't exist, create a new user
            const hashedPassword = await bcrypt.hash(password, 10);
            const newUser = await Users.create({
                username,
                password: hashedPassword,
            });

            return res.status(201).json({ message: 'Account created!', userId: newUser.user_id });
        }

        // If user exists, verify password
        const isMatch = await bcrypt.compare(password, user.password);
        if (!isMatch) return res.status(401).json({ message: 'Invalid credentials' });

        return res.json({ message: 'Login successful', userId: user.user_id });
    } catch (err) {
        console.error(err);
        res.status(500).json({ message: 'Internal server error' });
    }
});

// (File upload logic) configuration for Multer
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        const userId = req.headers['user-id']; // Retrieve userId from headers
        if (!userId) {
            return cb(new Error('User ID is required'), null);
        }

        const uploadPath = path.join(__dirname, 'images', userId); // Define upload path
        console.log("Destination path:", uploadPath);

        // Create directory if it does not exist
        if (!fs.existsSync(uploadPath)) {
            fs.mkdirSync(uploadPath, { recursive: true });
        }

        cb(null, uploadPath); // Pass the directory to Multer
    },
    filename: (req, file, cb) => {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        const filename = `${file.fieldname}-${uniqueSuffix}`;
        cb(null, filename); // Define unique filename
    },
});

const upload = multer({ storage });

// API to handle image uploads
app.post('/images/upload', upload.single('image'), async (req, res) => {
    try {
        const userId = req.headers['user-id']; // Retrieve userId from headers
        if (!userId) {
            return res.status(400).json({ error: 'User ID is required' });
        }

        const relativePath = path.join(userId, req.file.filename);
        console.log("File uploaded:", relativePath);

        // Save file path and user ID to the database
        await Images.create({
            user_id: userId,
            file_path: relativePath,
        });

        res.status(201).json({
            message: 'Image uploaded and metadata stored',
            imagePath: relativePath,
        });
    } catch (error) {
        console.error('Error handling upload:', error);
        res.status(500).json({ error: 'Server error while uploading image' });
    }
});

app.get('/images/:userId', async (req, res) => {
    const userId = req.headers['user-id'];
    try {
        // Fetch images from the database associated with the user
        const images = await Images.findAll({
            where: { user_id: userId }  // Find images by user ID
        });

        // Extract image paths
        const imagePaths = images.map(image => image.file_path);

        // Send the image paths as a response
        res.json(imagePaths);
    } catch (err) {
        console.error(err);
        res.status(500).send('Error fetching images');
    }
});

// Start the Express server
app.listen(5000, () => console.log('Server running on http://localhost:5000'));
