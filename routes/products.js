const express = require('express');
const router = express.Router();
const productController = require('../controllers/productController');

router.get('/', productController.getProducts);
router.get('/filter', productController.filterProducts);
router.get('/recommendation', productController.getRecommendations);
router.get('/:id', productController.getProductById);

module.exports = router;
