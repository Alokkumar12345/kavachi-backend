const { db } = require('../config/firebase');

exports.getProducts = async (req, res) => {
    try {
        const productsSnapshot = await db.collection('products').get();
        const products = productsSnapshot.docs.map(doc => doc.data());
        res.status(200).json(products);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

exports.getProductById = async (req, res) => {
    try {
        const { id } = req.params;
        const productDoc = await db.collection('products').doc(id).get();
        if (!productDoc.exists) return res.status(404).json({ error: 'Product not found' });
        res.status(200).json(productDoc.data());
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

exports.filterProducts = async (req, res) => {
    try {
        const { category, gender, color, size } = req.query;
        let query = db.collection('products');

        if (category) query = query.where('category', '==', category);
        if (gender) query = query.where('gender', '==', gender);
        if (color) query = query.where('color', 'array-contains', color);

        // Note: Firestore has limitations on multiple inequality/array-contains queries.
        // In a production app, Algolia or ElasticSearch is recommended for complex filtering.

        const snapshot = await query.get();
        const products = snapshot.docs.map(doc => doc.data());

        // Further in-memory filtering for size if needed
        const filtered = size ? products.filter(p => p.size.includes(size)) : products;

        res.status(200).json(filtered);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

exports.getRecommendations = async (req, res) => {
    try {
        // Simple recommendation logic placeholder
        const { userId } = req.query;
        // Fetch user profile, determine preferences or recent views
        // For now, return random products
        const productsSnapshot = await db.collection('products').limit(5).get();
        const products = productsSnapshot.docs.map(doc => doc.data());
        res.status(200).json(products);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};
