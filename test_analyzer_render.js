const { spawn } = require('child_process');
const path = require('path');

async function testPython() {
    const isProduction = process.env.NODE_ENV === 'production';
    const pythonCommand = isProduction ? path.join(__dirname, 'venv', 'bin', 'python') : 'python';
    const scriptPath = path.join(__dirname, 'analyzer', 'face_analyzer.py');

    console.log(`Testing Python: ${pythonCommand} ${scriptPath}`);

    const pythonProcess = spawn(pythonCommand, [scriptPath]);
    let pythonData = '';
    let pythonError = '';

    pythonProcess.stdout.on('data', (data) => pythonData += data.toString());
    pythonProcess.stderr.on('data', (data) => pythonError += data.toString());

    pythonProcess.on('close', (code) => {
        console.log(`Exit Code: ${code}`);
        console.log(`Stdout: ${pythonData}`);
        console.log(`Stderr: ${pythonError}`);
    });

    // Send a dummy base64 blank image
    const dummyImage = 'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
    pythonProcess.stdin.write(dummyImage);
    pythonProcess.stdin.end();
}

testPython();
