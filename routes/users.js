const express = require('express');
const router = express.Router();
const { updateProfile } = require('../controllers/userController');

// Define route
router.put('/profile', updateProfile);

module.exports = router;
