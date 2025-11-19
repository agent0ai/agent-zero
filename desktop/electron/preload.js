const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('agentZeroAPI', {
  listContainerImages: () => ipcRenderer.invoke('container:list-images'),
  getFlaskData: (endpoint, params) => ipcRenderer.invoke('flask:get-api-data', endpoint, params),
  
  getElectronVersion: () => process.versions.electron,
  getNodeVersion: () => process.versions.node,
  getChromiumVersion: () => process.versions.chrome,
});

contextBridge.exposeInMainWorld('launcher', {
  checkDocker: () => ipcRenderer.invoke('docker:check-status'),
  startDocker: () => ipcRenderer.invoke('docker:start'),
  launchMain: () => ipcRenderer.invoke('app:launch-main'),
});
