/**
 * REST API client & SSE Event Stream Manager
 */
const API = {
    async getTargets() {
        const res = await fetch('/api/targets');
        return res.json();
    },

    async addTarget(targetData) {
        const res = await fetch('/api/targets', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(targetData)
        });
        return res.json();
    },

    async deleteTarget(targetId) {
        const res = await fetch(`/api/targets/${targetId}`, { method: 'DELETE' });
        return res.json();
    },

    async forceCheck(targetId) {
        const res = await fetch(`/api/targets/${targetId}/check`, { method: 'POST' });
        return res.json();
    },

    async toggleTarget(targetId) {
        const res = await fetch(`/api/targets/${targetId}/toggle`, { method: 'POST' });
        return res.json();
    },

    async getSettings() {
        const res = await fetch('/api/settings');
        return res.json();
    },

    async updateSettings(settings) {
        const res = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        return res.json();
    },

    async getLogs() {
        const res = await fetch('/api/logs');
        return res.json();
    },

    async getAlerts() {
        const res = await fetch('/api/alerts');
        return res.json();
    },

    async getStrategies() {
        const res = await fetch('/api/strategies');
        return res.json();
    },

    async simulateAlert(movieTitle, theatre, bookingUrl) {
        const res = await fetch('/api/alerts/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ movie_title: movieTitle, theatre, booking_url: bookingUrl })
        });
        return res.json();
    },

    connectStream(onEvent) {
        const eventSource = new EventSource('/api/stream');
        eventSource.onmessage = (e) => {
            try {
                const payload = JSON.parse(e.data);
                onEvent(payload);
            } catch (err) {
                console.error("SSE parse error:", err);
            }
        };
        eventSource.onerror = (e) => {
            console.warn("SSE connection interrupted, retrying...", e);
        };
        return eventSource;
    }
};

window.API = API;
