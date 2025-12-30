

import * as device from "./device.js";
import * as api from "./api.js";
import { getUserTimezone } from "./time-utils.js";

export async function initialize(){
    // Initialize timezone (one-time setup from browser if not set in .env)
    await initializeTimezone();

    // set device class to body tag
    setDeviceClass();
}

async function initializeTimezone() {
    try {
        // Get browser timezone
        const timezone = getUserTimezone();

        // Calculate UTC offset in minutes
        const now = new Date();
        const offset_minutes = -now.getTimezoneOffset(); // Note: getTimezoneOffset returns opposite sign

        // Send to backend
        const response = await api.fetchApi("/init_timezone", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                timezone: timezone,
                offset_minutes: offset_minutes
            })
        });

        if (response.success) {
            console.log(`Timezone initialized: ${response.timezone}`);
        } else {
            console.log(`Timezone already set: ${response.timezone}`);
        }
    } catch (error) {
        console.error("Failed to initialize timezone:", error);
    }
}

function setDeviceClass(){
    device.determineInputType().then((type) => {
        // Remove any class starting with 'device-' from <body>
        const body = document.body;
        body.classList.forEach(cls => {
            if (cls.startsWith('device-')) {
                body.classList.remove(cls);
            }
        });
        // Add the new device class
        body.classList.add(`device-${type}`);
    });
}
