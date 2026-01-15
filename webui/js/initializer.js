

import * as device from "./device.js";

export async function initialize(){
    // set device class to body tag
    setDeviceClass();
    
    // Register Service Worker for PWA/Push
    registerServiceWorker();
}

function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/js/sw.js')
                .then(registration => {
                    console.log('SW registered: ', registration);
                })
                .catch(registrationError => {
                    console.error('SW registration failed: ', registrationError);
                });
        });
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
