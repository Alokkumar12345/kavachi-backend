const express = require('express');
const router = express.Router();
const faceAnalyzerController = require('../controllers/faceAnalyzerController');

router.post('/', faceAnalyzerController.analyzeFace);

module.exports = router;
