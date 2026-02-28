const admin = require('firebase-admin');

// Ensure you have your stringified Firebase Service Account JSON in the environment
// or you can load from a require('./serviceAccountKey.json')
console.log("== DEBUG FIREBASE CONFIG ==");
console.log("process.env.FIREBASE_SERVICE_ACCOUNT typeof:", typeof process.env.FIREBASE_SERVICE_ACCOUNT);
console.log("process.env.FIREBASE_SERVICE_ACCOUNT is falsy?", !process.env.FIREBASE_SERVICE_ACCOUNT);

try {
    if (process.env.FIREBASE_SERVICE_ACCOUNT) {
        console.log("Found FIREBASE_SERVICE_ACCOUNT env var, attempting to parse...");
        let serviceAccount;
        if (typeof process.env.FIREBASE_SERVICE_ACCOUNT === 'string') {
            serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
        } else {
            serviceAccount = process.env.FIREBASE_SERVICE_ACCOUNT;
        }

        // Force Google Cloud libraries to use this exact project ID
        process.env.GOOGLE_CLOUD_PROJECT = serviceAccount.project_id;

        admin.initializeApp({
            credential: admin.credential.cert(serviceAccount),
            projectId: serviceAccount.project_id
        });
        console.log("Firebase Admin Initialized Successfully!");
    } else {
        console.warn("Firebase Admin initialized without explicit credentials. Ensure you add serviceAccount logic.");
        admin.initializeApp();
    }
} catch (error) {
    console.error("Firebase Admin Initialization Error:", error);
}

const db = admin.firestore();
const auth = admin.auth();

module.exports = { admin, db, auth };
