const fs = require('fs');

async function testBackend() {
    try {
        console.log("Sending request to backend...");
        // 1x1 pixel base64 valid image
        const dummyImage = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=";
        const res = await fetch('http://localhost:5000/api/analyze-face', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                gender: 'Men',
                userId: 'test1234',
                image: dummyImage
            })
        });
        const data = await res.json();
        console.log("Backend Success! Response:", data);
    } catch (err) {
        console.error("Backend Error:", err.response ? err.response.data : err.message);
    }
}

testBackend();
