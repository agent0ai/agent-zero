const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('node:path');
const { exec, spawn } = require('node:child_process');
const http = require('node:http');

let mainWindow;

function createWindow() {
  const iconPath = path.join(app.getAppPath(), 'assets', process.platform === 'win32' ? 'icon.ico' : 'icon.png');
  
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 768,
    minWidth: 800,
    minHeight: 600,
    title: "Agent Zero Desktop",
    icon: iconPath,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(app.getAppPath(), 'preload.js'),
      sandbox: true
    }
  });

  // Load the Wizard first
  mainWindow.loadFile(path.join(__dirname, 'wizard.html'));

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http:') || url.startsWith('https:')) {
      shell.openExternal(url);
    }
    return { action: 'deny' };
  });

  // Open DevTools if in development or if requested via env var
  if (true || !app.isPackaged || process.env.OPEN_DEVTOOLS === 'true') {
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  }
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// IPC Handlers

// Check if Docker backend is responding
ipcMain.handle('docker:check-status', async () => {
  console.log('[IPC] Checking Docker status...');
  return new Promise((resolve) => {
    const req = http.get('http://localhost:80/health', { timeout: 2000 }, (res) => {
      // Accept any success code or redirect, or even 404 if it means the server is there
      if (res.statusCode < 500) { 
        resolve(true);
      } else {
        console.log('Docker check failed with status:', res.statusCode);
        resolve(false);
      }
    });

    req.on('timeout', () => {
      console.log('Docker check timed out');
      req.destroy();
      resolve(false);
    });

    req.on('error', (e) => {
      // console.log('Docker check error:', e.message); // verbose
      resolve(false);
    });
    
    req.end();
  });
});

// Start Docker Container
ipcMain.handle('docker:start', async () => {
  console.log('[IPC] Starting Docker...');
  // Root of the repo (assumed to be 3 levels up from desktop/electron/main.js)
  // desktop/electron/main.js -> desktop/electron -> desktop -> root
  const repoRoot = path.resolve(__dirname, '../../'); 
  
  return new Promise((resolve) => {
    // Check if running
    exec('docker ps -q -f name=agent-zero', (err, stdout) => {
      if (stdout && stdout.trim().length > 0) {
        return resolve({ success: true, message: 'Already running' });
      }

      // Check if exists but stopped
      exec('docker ps -aq -f name=agent-zero', (err, stdout) => {
        if (stdout && stdout.trim().length > 0) {
          // Start existing
          exec('docker start agent-zero', (err) => {
            if (err) return resolve({ success: false, error: err.message });
            resolve({ success: true, message: 'Started existing container' });
          });
        } else {
          // Run new
          // Using port 80:80 as requested
          // Mounting repoRoot to /a0
          const cmd = `docker run -d -p 80:80 -v "${repoRoot}":/a0 --name agent-zero agent0ai/agent-zero`;
          console.log("Running:", cmd);
          
          exec(cmd, { maxBuffer: 1024 * 1024 * 10 }, (err) => {
            if (err) return resolve({ success: false, error: err.message });
            resolve({ success: true, message: 'Created and started new container' });
          });
        }
      });
    });
  });
});

// Switch to Main App
ipcMain.handle('app:launch-main', () => {
  if (mainWindow) {
    mainWindow.loadURL('http://localhost:80');
  }
});

// Example: List Docker Images
// IPC Handlers

// Example: List Docker Images
ipcMain.handle('container:list-images', async (event) => {
  return new Promise((resolve, reject) => {
    exec('docker images --format "{{.Repository}}\t{{.Tag}}\t{{.ID}}"', (error, stdout, stderr) => {
      if (error) {
        console.error(`exec error: ${error.message}`);
        return reject(`Failed to list images: ${error.message}`);
      }
      const images = stdout.split('\n').filter(line => line.trim() !== '').map(line => {
        const parts = line.split('\t');
        return {
          repository: parts[0],
          tag: parts[1],
          id: parts[2]
        };
      });
      resolve(images);
    });
  });
});

// Example: Proxy Flask API calls
ipcMain.handle('flask:get-api-data', async (event, endpoint, params = {}) => {
  if (!endpoint.startsWith('/api/')) {
     throw new Error('Invalid Flask API endpoint');
  }

  const url = new URL(`http://localhost:80${endpoint}`);
  Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));

  try {
    const response = await fetch(url.toString(), {
      headers: {
        'X-API-KEY': process.env.MCP_SERVER_TOKEN || '',
        // Note: Cookie handling might need more sophisticated logic if sessions are strict
      }
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error fetching from Flask API ${endpoint}:`, error);
    throw error;
  }
});
