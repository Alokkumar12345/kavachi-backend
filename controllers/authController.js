const { db, auth } = require('../config/firebase');

exports.signup = async (req, res) => {
    try {
        const { name, email, password, gender } = req.body;

        const userRecord = await auth.createUser({
            email,
            password,
            displayName: name,
        });

        const userDoc = {
            id: userRecord.uid,
            name,
            email,
            gender,
            skinTone: null,
            savedAddresses: [],
            orderHistory: [],
            wishlist: [],
            createdAt: new Date().toISOString()
        };

        await db.collection('users').doc(userRecord.uid).set(userDoc);

        res.status(201).json({ message: 'User created successfully', user: userDoc });
    } catch (error) {
        console.error("Signup Error in backend:", error);
        res.status(500).json({ error: error.message });
    }
};

exports.login = async (req, res) => {
    try {
        const { idToken } = req.body;
        if (!idToken) return res.status(400).json({ error: 'ID token is required' });

        // Verify Firebase identity securely via backend Admin SDK
        const decodedToken = await auth.verifyIdToken(idToken);
        const userRef = db.collection('users').doc(decodedToken.uid);
        const userDoc = await userRef.get();

        let userData;

        if (!userDoc.exists) {
            // Missing Firestore document (perhaps signed up via standard Firebase client)
            // Create their Firestore document dynamically
            userData = {
                id: decodedToken.uid,
                name: decodedToken.name || 'User',
                email: decodedToken.email,
                gender: 'Unspecified',
                skinTone: null,
                savedAddresses: [],
                orderHistory: [],
                wishlist: [],
                createdAt: new Date().toISOString(),
                authProvider: decodedToken.firebase.sign_in_provider
            };
            await userRef.set(userData);
        } else {
            // User exists, retrieve their DB payload
            userData = userDoc.data();
        }

        res.status(200).json({ message: 'Login successful', user: userData });
    } catch (error) {
        console.error("Login Error in backend:", error.message);
        res.status(401).json({ error: 'Invalid token or login failed', details: error.message });
    }
};
