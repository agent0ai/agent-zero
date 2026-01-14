import { createStore } from "/js/AlpineStore.js";

/**
 * Microphone selector store for managing audio input device selection
 * @typedef {Object} MicrophoneSettingStore
 * @property {Array<MediaDeviceInfo>} devices - All available audio input devices
 * @property {string} selectedDevice - Currently selected device ID
 * @property {boolean} requestingPermission - Whether microphone permission is being requested
 * @property {?number} permissionTimer - Timer for polling device availability
 * @property {number} permissionAttempts - Number of device polling attempts
 * @property {Function} init - Initialize the store, load saved device preference
 * @property {Function} loadDevices - Load available audio input devices from browser
 * @property {Function} requestPermission - Request microphone permission from user
 * @property {Function} pollForDevices - Poll for devices until found or timeout
 * @property {Function} selectDevice - Select a device by ID
 * @property {Function} onSelectDevice - Handle device selection change, save to localStorage
 * @property {Function} getSelectedDevice - Get the MediaDeviceInfo object for selected device
 */

const model = {


    devices: [],
    selectedDevice: "",

    async init() {
        // Load selected device from localStorage if present
        const saved = localStorage.getItem('microphoneSelectedDevice');
        await this.loadDevices();
        if (saved && this.devices.some(d => d.deviceId === saved)) {
            this.selectedDevice = saved;
        }
    },

    async loadDevices() {
        // Get media devices
        const devices = await navigator.mediaDevices.enumerateDevices();
        // Filter for audio input (microphones)
        this.devices = devices.filter(d => d.kind === "audioinput" && d.deviceId);
        // Set selected device to first available, if any
        this.selectedDevice = this.devices.length > 0 ? this.devices[0].deviceId : "";
    },

    // track permission request state
    requestingPermission: false,
    permissionTimer: null,
    permissionAttempts: 0,
    
    // request microphone permission and poll for devices
    async requestPermission() {
        // set flag first so UI can update immediately
        clearTimeout(this.permissionTimer);
        this.requestingPermission = true;
        this.permissionAttempts = 0;
        
        // request permission in next tick to allow UI to update
        setTimeout(async () => {
            try {
                await navigator.mediaDevices.getUserMedia({ audio: true });
                // start polling for devices
                this.pollForDevices();
            } catch (err) {
                console.error("[Microphone Selector] Microphone permission denied");
                this.requestingPermission = false;
            }
        }, 0);
    },
    
    // poll for devices until found or timeout (60s)
    async pollForDevices() {
        await this.loadDevices();
        
        // check if we found devices with valid IDs
        if (this.devices.some(d => d.deviceId && d.deviceId !== "") || this.permissionAttempts >= 60) {
            this.requestingPermission = false;
            return;
        }
        
        // continue polling
        this.permissionAttempts++;
        this.permissionTimer = setTimeout(() => this.pollForDevices(), 1000);
    },

    async selectDevice(deviceId) {
        this.selectedDevice = deviceId;
        this.onSelectDevice();
    },

    async onSelectDevice() {
        localStorage.setItem('microphoneSelectedDevice', this.selectedDevice);
    },

    getSelectedDevice() {
        let device = this.devices.find(d => d.deviceId === this.selectedDevice);
        if (!device && this.devices.length > 0) {
            device = this.devices.find(d => d.deviceId === "default") || this.devices[0];
        }
        return device;
    }

};

const store = createStore("microphoneSetting", model);

export { store };
