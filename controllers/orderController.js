const { db } = require('../config/firebase');

exports.createOrder = async (req, res) => {
    try {
        const { userId, items, totalAmount, paymentMethod, address } = req.body;

        // Expected Delivery Date Logic (Current + 5 days)
        const orderDate = new Date();
        const deliveryDate = new Date();
        deliveryDate.setDate(orderDate.getDate() + 5);

        const orderData = {
            userId,
            items,
            totalAmount,
            paymentMethod,
            address,
            status: 'Processing',
            orderDate: orderDate.toISOString(),
            expectedDeliveryDate: deliveryDate.toISOString(),
        };

        const docRef = await db.collection('orders').add(orderData);

        // Also clear the user's cart (ideally in a batch write)
        const cartSnapshot = await db.collection('cart').where('userId', '==', userId).get();
        const batch = db.batch();
        cartSnapshot.docs.forEach((doc) => {
            batch.delete(doc.ref);
        });
        await batch.commit();

        res.status(201).json({ message: 'Order created successfully', orderId: docRef.id, expectedDelivery: deliveryDate });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

exports.getUserOrders = async (req, res) => {
    try {
        const { userId } = req.params;
        const snapshot = await db.collection('orders').where('userId', '==', userId).get();
        const orders = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
        res.status(200).json(orders);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};
