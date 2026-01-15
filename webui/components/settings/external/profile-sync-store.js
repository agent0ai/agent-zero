import { callJsonApi } from "/js/api.js";

const model = {
    profile: null,
    loading: false,
    error: null,
    pushEnabled: false,
    isAndroid: /Android/i.test(navigator.userAgent),
    isApple: /iPhone|iPad|iPod/i.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1),
    
    async init() {
        await this.loadProfile();
        this.checkPushStatus();
    },

    async checkPushStatus() {
        if ('Notification' in window && Notification.permission === 'granted') {
            this.pushEnabled = true;
        }
    },

    async enablePushNotifications() {
        if (!('Notification' in window) || !('serviceWorker' in navigator)) {
            alert("Your browser does not support push notifications.");
            return;
        }

        try {
            const permission = await Notification.requestPermission();
            if (permission !== 'granted') throw new Error("Permission not granted");

            // Fetch correctly generated VAPID key from server
            const keyResp = await callJsonApi("/profile_sync", { action: "get_push_key" });
            if (!keyResp.success) throw new Error("Could not fetch server push key");
            const vapidPublicKey = keyResp.publicKey;
            
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(vapidPublicKey)
            });

            // Send subscription to server
            await callJsonApi("/profile_sync", {
                action: "update_push_subscription",
                subscription: subscription
            });

            this.pushEnabled = true;
            if (window.toast) toast("Push notifications enabled!", "success");
        } catch (err) {
            console.error("Failed to enable push", err);
            alert("Error: " + err.message);
        }
    },

    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    },
    
    async loadProfile() {
        try {
            const resp = await callJsonApi("/profile_sync", { action: "get_profile" });
            if (resp.success) {
                this.profile = resp.profile;
            }
        } catch (err) {
            console.error("Failed to load profile", err);
        }
    },
    
    async syncAndroidProfile() {
        this.loading = true;
        this.error = null;
        try {
            // Android-specific profile gathering
            // In a real scenario, this would use Digital Credentials API or Google Identity
            // For this implementation, we use available Web APIs to simulate "Full Sharing"
            
            const profileData = {
                fullName: "Android Admin", 
                email: "admin@android.local",
                phone: null,
                avatarUrl: null,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                locale: navigator.language,
                deviceInfo: {
                    userAgent: navigator.userAgent,
                    platform: navigator.platform,
                    memory: navigator.deviceMemory,
                    cores: navigator.hardwareConcurrency,
                    connection: navigator.connection ? {
                        type: navigator.connection.effectiveType,
                        downlink: navigator.connection.downlink,
                        rtt: navigator.connection.rtt
                    } : 'unknown',
                    battery: null
                }
            };

            // Get Battery Status if available (common on Chrome/Android)
            if (navigator.getBattery) {
                const battery = await navigator.getBattery();
                profileData.deviceInfo.battery = {
                    level: battery.level * 100,
                    charging: battery.charging
                };
            }
            
            // If on Android and supported, try to get specific credential info
            if (window.DigitalCredential) {
                // Future: implementation of Digital Credentials API
            }

            const resp = await callJsonApi("/profile_sync", {
                action: "update_profile",
                profile: profileData
            });
            
            if (resp.success) {
                this.profile = profileData;
                alert("Android Profile Synced Successfully!");
            } else {
                throw new Error(resp.error);
            }
            
        } catch (err) {
            this.error = err.message;
        } finally {
            this.loading = false;
        }
    },

    async syncAppleProfile() {
        this.loading = true;
        this.error = null;
        try {
            const profileData = {
                fullName: "Apple User", 
                email: "user@icloud.local",
                phone: null,
                avatarUrl: null,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                locale: navigator.language,
                deviceInfo: {
                    userAgent: navigator.userAgent,
                    platform: navigator.platform,
                    touchPoints: navigator.maxTouchPoints,
                    pixelRatio: window.devicePixelRatio,
                    screen: `${window.screen.width}x${window.screen.height}`,
                    prefersDarkMode: window.matchMedia('(prefers-color-scheme: dark)').matches,
                    isStandalone: !!window.navigator.standalone
                }
            };
            
            const resp = await callJsonApi("/profile_sync", {
                action: "update_profile",
                profile: profileData
            });
            
            if (resp.success) {
                this.profile = profileData;
                alert("Apple (iOS) Profile Synced Successfully!");
            } else {
                throw new Error(resp.error);
            }
            
        } catch (err) {
            this.error = err.message;
        } finally {
            this.loading = false;
        }
    }
};

export const store = model;
