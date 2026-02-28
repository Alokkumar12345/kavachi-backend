const { db } = require('../config/firebase');

exports.addToCart = async (req, res) => {
    try {
        const { userId, productId, quantity, size, color } = req.body;

        // In a real app, generate a unique ID for the cart item or compound key
        const cartItemId = `${userId}_${productId}_${size}_${color}`;

        const cartItem = {
            userId,
            productId,
            quantity: quantity || 1,
            size,
            color,
            addedAt: new Date().toISOString()
        };

        await db.collection('cart').doc(cartItemId).set(cartItem, { merge: true });

        res.status(200).json({ message: 'Added to cart successfully', item: cartItem });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

exports.getCart = async (req, res) => {
    try {
        const { userId } = req.params;
        const snapshot = await db.collection('cart').where('userId', '==', userId).get();

        const cartItems = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
        res.status(200).json(cartItems);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

exports.removeFromCart = async (req, res) => {
    try {
        const { id } = req.params;
        await db.collection('cart').doc(id).delete();
        res.status(200).json({ message: 'Item removed from cart' });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};
