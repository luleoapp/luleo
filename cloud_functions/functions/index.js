const functions = require("firebase-functions");
const admin = require("firebase-admin");
const axios = require("axios");

// Initialize Firebase Admin SDK
admin.initializeApp();

// Get Firestore database instance
const db = admin.firestore();

/**
 * Retrieves the current Cloud Run URL from Firestore
 * @returns {Promise<string>} The current Cloud Run URL
 */
async function get_cloud_run_url() {
    try {
        const addressDocRef = db.collection('service_layer').doc('curr');
        const addressDoc = await addressDocRef.get();
        if (!addressDoc.exists) {
            throw new Error('Cloud Run URL document does not exist');
        }
        const addressDict = addressDoc.data();
        return addressDict['curr'];
    } catch (error) {
        console.error('Error fetching Cloud Run URL:', error);
        throw error;
    }
}

// Cloud Function triggered on new document creation in 'user_inputs' collection
exports.triggerCloudRunOnCreate = functions.firestore
    .document('user_inputs/{uploadId}')
    .onCreate(async (snap, context) => {
        try {
            const newData = snap.data(); 
            console.log('New document data:', newData);

            const uploadId = context.params.uploadId;
            console.log('Upload ID:', uploadId);

            const cloudRunUrl = "https://process-daily-narrative-418435618601.us-central1.run.app"
            console.log('Cloud Run URL:', cloudRunUrl);

            // Prepare payload for Cloud Run
            const payload = {
                "REQUEST_TYPE": "PROCESS_USER_UPLOAD",
                "PARAMS": {
                    "upload_id": uploadId
                }
            };

            // Make POST request to Cloud Run
            const response = await axios.post(cloudRunUrl, payload, {
            });
            console.log('Cloud Run Response:', response.data);
        } catch (error) {
            console.error('Error in triggerCloudRunOnCreate:', error);
            // Consider adding more robust error handling or retries here
        }
    });