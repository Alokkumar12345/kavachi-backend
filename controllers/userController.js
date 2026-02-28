const { db } = require('../config/firebase');

exports.updateProfile = async (req, res) => {
    try {
        const { userId, name, gender, profileImage } = req.body;

        if (!userId) {
            return res.status(400).json({ success: false, message: 'User ID is required' });
        }

        // Get reference to the specific user document
        const userRef = db.collection('users').doc(userId);
        const userDoc = await userRef.get();

        if (!userDoc.exists) {
            return res.status(404).json({ success: false, message: 'User not found in database' });
        }

        // Prepare the payload to defensively merge existing fields vs new ones
        const updateData = {};
        if (name !== undefined) updateData.name = name;
        if (gender !== undefined) updateData.gender = gender;
        if (profileImage !== undefined) updateData.profileImage = profileImage;

        await userRef.update({
            ...updateData,
            updatedAt: new Date().toISOString()
        });

        // Refetch the most atomic up-to-date document to send back to the frontend Context
        const updatedDoc = await userRef.get();

        res.json({
            success: true,
            user: { id: updatedDoc.id, ...updatedDoc.data() }
        });
    } catch (error) {
        console.error('Error updating user profile:', error);
        res.status(500).json({ success: false, message: 'Server error updating profile' });
    }
};
