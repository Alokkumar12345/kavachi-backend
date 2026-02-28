// A 1x1 black pixel base64 image
const dummyImage = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=';

async function testFaceAnalyzer() {
    console.log("Analyzing dummy image on Render...");
    try {
        const res = await fetch('https://kavachi-backend-1.onrender.com/api/analyze-face', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                gender: 'Men',
                image: dummyImage
            })
        });

        const status = res.status;
        const text = await res.text();
        console.log(`HTTP Status: ${status}`);

        try {
            const data = JSON.parse(text);
            console.log("Response JSON:", JSON.stringify(data, null, 2));
        } catch (e) {
            console.log("Response Text:", text);
        }

    } catch (err) {
        console.error("Fetch failed:", err.message);
    }
}

testFaceAnalyzer();
