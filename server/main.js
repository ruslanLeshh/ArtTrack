const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const bcrypt = require('bcrypt');
const { Pool } = require('pg');
 
const sequelize = require('./sequelize');
const Users = require('./models/users');
const Images = require('./models/images');
const Matches = require('./models/matches');

const multer = require('multer'); // For handling file uploads
const path = require('path');
const fs = require('fs');
const { log } = require('console');
const { Op } = require('sequelize');

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

// (File upload logic) configuration for Multer + one who uploads the file
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        const uploadPath = path.join(__dirname, 'images', 'users-images');
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
app.post('/images/users-images', upload.single('image'), async (req, res) => {
    try {
        const userId = req.headers['user-id']; // Retrieve userId from headers
        if (!userId) {
            return res.status(400).json({ error: 'User ID is required' });
        }
        // Save filename and user ID to the database
        await Images.create({
            user_id: userId,
            filename: req.file.filename,
        });

        res.status(201).json({
            message: 'Image table succesfully updated',
            filename: req.file.filename,   // for front to display
        }); 
    } catch (error) {
        console.error('Error handling upload:', error);
        res.status(500).json({ error: 'Server error while uploading image' });
    }
});

app.get('/images/:userId', async (req, res) => {
    try {
        userId = req.params.userId;
        // Fetch images from the database associated with the user
        const images = await Images.findAll({
            where: { user_id: userId }  // Find images by user ID
        });

        const filenames = images.map(image => image.filename);

        res.json(filenames); // Send filenames as a response
    } catch (err) {
        console.error('Error fetching images:', err);
        res.status(500).json({ error: 'Error fetching images' });
    }
});

function formatFilename(filename) {
    // Step 1: Replace underscores with spaces
    let formattedFilename = filename.replace(/_/g, ' ');

    // Step 2: Add 'File:' at the beginning
    formattedFilename = 'File:' + formattedFilename;

    return formattedFilename;
}

const Papa = require('papaparse');

async function getUrlFromCsv(filename) {
    try {
        const decodedFilename = decodeURIComponent(filename).trim();
        filename = formatFilename(decodedFilename);
        // console.log("filename:", filename);
        
        // Read the CSV file from the local file system
        const csvFilePath = path.join(__dirname, 'absolutely_legal_metadata.csv');  
        const csvText = fs.readFileSync(csvFilePath, 'utf-8');  

        // Parse the CSV text using PapaParse
        const parsedData = Papa.parse(csvText, {
            header: true,         // Treat the first row as headers
            dynamicTyping: true,  // Automatically convert number-like strings to numbers
            skipEmptyLines: true, // Skip empty lines
        });

        // Find the row where the filename matches
        const matchedRow = parsedData.data.find(row => row.title === filename);  // Assuming 'title' column holds filenames

        if (matchedRow) {
            // Return the URL if a match is found
            return matchedRow.url;  
        } else {
            // If no matching file is found, throw an error
            throw new Error(`Filename ${filename} not found in CSV.`);
        }
    } catch (error) {
        console.error('Error fetching or parsing CSV file:', error);
        throw error; 
    }
}


app.get('/matches/:userId', async (req, res) => {
    try {
        userId = req.params.userId;
        // console.log('User ID:', userId);

        // Fetch images related to the user_id (Assuming Images model is defined)
        const images = await Images.findAll({
            where: { user_id: userId }  // Filter Images by user_id
        });
        // console.log("images:",images)
        if (images.length === 0) {
            console.log("NO IMAGES")
            return res.status(404).json({ message: 'No images found for the user.' });
        }

        // Fetch matches for the images (Assuming Matches and Images models are related)
        const matches = await Matches.findAll({
            include: [{
                model: Images,  // Include the Images model to link Matches to Images
                where: {
                    image_id: {
                        [Op.in]: images.map(image =>  image.dataValues.image_id)  // Check if image_id matches one of the user's image IDs
                    }
                }
            }]
        });
        // console.log("matches:",matches)
        if (matches.length === 0) {
            // console.log("NO MATCHES")
            return res.status(404).json({ message: 'No matches found.' });
        }

        // Fetch image URLs asynchronously for each match
        const matchResults = await Promise.all(matches.map(async (match) => {
            try {
                // Fetch the URL for each match's new_image_filename
                const imageUrl = await getUrlFromCsv(match.new_image_filename);

                return {
                    match_id: match.match_id,
                    similarity_score: match.similarity_score,
                    new_image_filename: match.new_image_filename,  // Get the filename from the included Image model
                    matched_image_filename: match.matched_image_filename,
                    image_url: imageUrl
                };
            } catch (error) {
                console.error(`Error fetching URL for ${match.new_image_filename}:`, error);
                return {
                    match_id: match.match_id,
                    similarity_score: match.similarity_score,
                    new_image_filename: match.new_image_filename,
                    matched_image_filename: match.matched_image_filename,
                    image_url: null,  // If there is an error fetching the URL, set it to null
                };
            }
        }));

        console.log("MATCHES", matchResults)
        
        res.json({ matches: matchResults }); // send results 

    } catch (error) {
        console.error('Error fetching matches:', error);
        res.status(500).json({ error: 'An error occurred while fetching matches.' });
    }
});

// Start the Express server
app.listen(5000, () => console.log('Server running on http://localhost:5000'));
