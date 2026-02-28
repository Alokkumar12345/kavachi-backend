const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');

dotenv.config();

const app = express();

// Middleware
app.use(cors());
app.use(express.json({ limit: '10mb' }));

// Routes
app.use('/api/auth', require('./routes/auth'));
app.use('/api/users', require('./routes/users'));
app.use('/api/products', require('./routes/products'));
app.use('/api/analyze-face', require('./routes/faceAnalyzer'));
app.use('/api/cart', require('./routes/cart'));
app.use('/api/orders', require('./routes/orders'));

app.get('/api/health', (req, res) => {
  const { admin } = require('./config/firebase');
  const fs = require('fs');
  const path = require('path');
  const venvPath = path.join(process.cwd(), 'venv', 'bin', 'python');

  res.json({
    status: 'ok',
    version: '1.0.3-cwd',
    firebaseInitialized: !!admin.apps.length,
    environment: process.env.NODE_ENV || 'development',
    cwd: process.cwd(),
    venvExists: fs.existsSync(venvPath)
  });
});

app.get('/api/test-analyzer', async (req, res) => {
  const { spawn } = require('child_process');
  const path = require('path');
  const fs = require('fs');
  const isProduction = process.env.NODE_ENV === 'production';
  const pythonCommand = isProduction ? path.join(process.cwd(), 'venv', 'bin', 'python') : 'python';
  const scriptPath = path.join(process.cwd(), 'analyzer', 'face_analyzer.py');

  let stdout = '';
  let stderr = '';

  if (!fs.existsSync(scriptPath)) return res.status(404).json({ error: 'Script not found at ' + scriptPath });

  const pythonProcess = spawn(pythonCommand, [scriptPath]);

  pythonProcess.stdout.on('data', (data) => stdout += data.toString());
  pythonProcess.stderr.on('data', (data) => stderr += data.toString());

  pythonProcess.on('close', (code) => {
    res.json({
      code,
      stdout,
      stderr,
      pythonCommand,
      scriptPath,
      exists: require('fs').existsSync(pythonCommand)
    });
  });

  const dummyImage = 'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
  pythonProcess.stdin.write(dummyImage);
  pythonProcess.stdin.end();
});

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = app;

