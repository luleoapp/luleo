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
        return addressDict['cloud_run_url'];
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
            const uploadId = context.params.uploadId;
            console.log('Upload ID:', uploadId);
            const cloud_run_url = await get_cloud_run_url();
            console.log('Cloud Run URL:', cloud_run_url);
            const response = await axios.post(cloud_run_url, {
                REQUEST_TYPE: "PROCESS_USER_UPLOAD",
                PARAMS: {
                    upload_id: uploadId,
                }
            });
            console.log(`Got response: ${JSON.stringify(response.data)}`);
        } catch (error) {
            console.error('Error in triggerCloudRunOnCreate:', error);
            // Consider adding more robust error handling or retries here
        }
    });