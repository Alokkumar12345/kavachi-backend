const { db } = require('../config/firebase');
const { spawn } = require('child_process');
const path = require('path');

exports.analyzeFace = async (req, res) => {
    try {
        const { gender, image } = req.body; // 'image' should be base64 string

        if (!gender || !image) {
            return res.status(400).json({ error: 'Gender and image are required' });
        }

        // 1. Spawn Python Script
        const scriptPath = path.join(__dirname, '..', 'analyzer', 'face_analyzer.py');
        const pythonProcess = spawn('python', [scriptPath]);

        // 2. Pass Base64 image to Python
        let pythonData = '';
        let pythonError = '';

        const pythonPromise = new Promise((resolve, reject) => {
            pythonProcess.stdout.on('data', (data) => {
                pythonData += data.toString();
            });

            pythonProcess.stderr.on('data', (data) => {
                pythonError += data.toString();
                console.error("Python Stderr:", data.toString());
            });

            pythonProcess.on('close', (code) => {
                if (code !== 0) {
                    reject(new Error(`Analyzer failed: ${pythonError || 'Unknown error'}`));
                } else {
                    try {
                        const result = JSON.parse(pythonData);
                        if (result.error) reject(new Error(result.error));
                        else resolve(result);
                    } catch (e) {
                        reject(new Error("Failed to parse python response: " + pythonData));
                    }
                }
            });

            // Write image to stdin and close it
            pythonProcess.stdin.write(image);
            pythonProcess.stdin.end();
        });

        const cvResult = await pythonPromise;
        const skinTone = cvResult.detectedTone || 'Medium'; // Fallback
        console.log(`ML Detected Skin Tone: ${skinTone}`);

        // Determine the style profile based on skin tone and gender
        let recommendedPalette = [];
        let styleSuggestions = "";

        // Map new Python Tone Strings to product lookup categories
        const exactTone = skinTone;
        let mappedCategory = 'Neutral'; // Fallback

        switch (exactTone) {
            case 'Sun-Kissed Warmth':
            case 'Golden Glow':
            case 'Warm Bronze Glow':
            case 'Caramel Warmth':
            case 'Soft Almond':
                recommendedPalette = ['Terracotta', 'Warm Gold', 'Peach', 'Emerald'];
                styleSuggestions = `Warm and rich colors complement your ${exactTone} beautifully.`;
                mappedCategory = 'Warm';
                break;
            case 'Rosy Cool':
            case 'Soft Rosy':
            case 'Porcelain Light':
            case 'Cool Ash Undertone':
                recommendedPalette = ['Rose Pink', 'Mint Blue', 'Lavender', 'Silver'];
                styleSuggestions = `Cool, pastel, and jewel tones harmonize with your ${exactTone}.`;
                mappedCategory = 'Cool';
                break;
            case 'Olive Undertone':
            case 'Natural Tan':
            case 'Deep Cocoa':
            case 'Balanced Neutral':
            default:
                recommendedPalette = ['Charcoal', 'Moss Green', 'Taupe', 'Burgundy'];
                styleSuggestions = `Earthy and neutral shades create a stunning contrast with your ${exactTone}.`;
                mappedCategory = 'Neutral';
                break;
        }

        // Fetch recommended products from Firestore
        const productsSnapshot = await db.collection('products')
            .where('gender', '==', gender)
            .where('skinToneRecommended', 'array-contains', mappedCategory)
            .limit(10)
            .get();

        const recommendedProducts = productsSnapshot.docs.map(doc => doc.data());

        // If no exact match, fallback to some default generic products for that gender
        let finalProducts = recommendedProducts;
        if (finalProducts.length === 0) {
            const fallback = await db.collection('products').where('gender', '==', gender).limit(5).get();
            finalProducts = fallback.docs.map(d => d.data());
        }

        // Save the result to the user's profile if they are logged in
        const { userId } = req.body;
        console.log(`Extracting userId from request payload: ${userId}`);

        if (userId) {
            try {
                console.log(`Attempting to update user profile ${userId} with skinTone: ${skinTone}`);
                await db.collection('users').doc(userId).update({ skinTone });
                console.log(`Successfully updated Firestore user document: ${userId}`);
            } catch (err) {
                console.error("Failed to update user skin tone in Firestore:", err);
                // Do not crash the response if profile update fails
            }
        } else {
            console.log("No userId was provided in the Face Analysis payload. Database update skipped.");
        }

        res.status(200).json({
            profile: { gender, skinTone },
            recommendations: {
                palette: recommendedPalette,
                styleSuggestions: styleSuggestions,
                products: finalProducts
            }
        });

    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};
