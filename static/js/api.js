/**
 * REST API client & SSE Event Stream Manager
 * Supports dynamic Flask backend API or static GitHub Pages fallback mode.
 */
const API = {
    async _fetchJSON(url, options = {}) {
        try {
            const res = await fetch(url, options);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (e) {
            console.warn(`[API] Fallback mode active for ${url}:`, e.message);
            return null; // Fallback indicator
        }
    },

    async getTargets() {
        const data = await this._fetchJSON('/api/targets');
        if (data) return data;
        
        // Static Fallback
        const stored = localStorage.getItem('mtt_targets');
        if (stored) return JSON.parse(stored);
        const defaultTargets = [
            {
                "id": "target-victory-toxic",
                "movie_title": "Toxic: A Fairy Tale for Grown Ups (Kannada)",
                "theatre": "Victory Cinema, Kamakshipalya",
                "website": "https://victorycinema.in/",
                "target_url": "https://victorycinema.in/showing/",
                "strategy_id": "victory_cinema",
                "interval_sec": 15,
                "enabled": true,
                "last_status": "PENDING",
                "last_checked": new Date().toISOString(),
                "last_latency_ms": 142
            }
        ];
        localStorage.setItem('mtt_targets', JSON.stringify(defaultTargets));
        return defaultTargets;
    },

    async addTarget(targetData) {
        const data = await this._fetchJSON('/api/targets', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(targetData)
        });
        if (data) return data;

        // Static Fallback
        const targets = await this.getTargets();
        const newTarget = {
            id: `target-${Date.now()}`,
            ...targetData,
            enabled: true,
            last_status: "PENDING",
            last_checked: new Date().toISOString(),
            last_latency_ms: 120
        };
        targets.push(newTarget);
        localStorage.setItem('mtt_targets', JSON.stringify(targets));
        return newTarget;
    },

    async deleteTarget(targetId) {
        const data = await this._fetchJSON(`/api/targets/${targetId}`, { method: 'DELETE' });
        if (data) return data;

        const targets = (await this.getTargets()).filter(t => t.id !== targetId);
        localStorage.setItem('mtt_targets', JSON.stringify(targets));
        return { success: true };
    },

    async forceCheck(targetId) {
        const data = await this._fetchJSON(`/api/targets/${targetId}/check`, { method: 'POST' });
        if (data) return data;

        return {
            status: "NO_TICKETS",
            latency_ms: Math.floor(Math.random() * 100) + 100,
            details: "Checked (Static Preview Mode)"
        };
    },

    async toggleTarget(targetId) {
        const data = await this._fetchJSON(`/api/targets/${targetId}/toggle`, { method: 'POST' });
        if (data) return data;

        const targets = await this.getTargets();
        const target = targets.find(t => t.id === targetId);
        if (target) {
            target.enabled = !target.enabled;
            localStorage.setItem('mtt_targets', JSON.stringify(targets));
            return target;
        }
        return { id: targetId, enabled: false };
    },

    async getSettings() {
        const data = await this._fetchJSON('/api/settings');
        if (data) return data;

        const stored = localStorage.getItem('mtt_settings');
        return stored ? JSON.parse(stored) : {
            sound_enabled: true,
            desktop_notifications: true,
            voice_alerts: true,
            telegram_webhook_url: "",
            discord_webhook_url: "",
            custom_webhook_url: ""
        };
    },

    async updateSettings(settings) {
        const data = await this._fetchJSON('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        if (data) return data;

        localStorage.setItem('mtt_settings', JSON.stringify(settings));
        return settings;
    },

    async getLogs() {
        const data = await this._fetchJSON('/api/logs');
        if (data) return data;

        const stored = localStorage.getItem('mtt_logs');
        return stored ? JSON.parse(stored) : [
            {
                timestamp: new Date().toISOString(),
                movie_title: "Toxic (Kannada)",
                status: "CHECKING",
                latency_ms: 154,
                details: "GitHub Pages Static Mode — Backend Engine Active"
            }
        ];
    },

    async getAlerts() {
        const data = await this._fetchJSON('/api/alerts');
        if (data) return data;

        const stored = localStorage.getItem('mtt_alerts');
        return stored ? JSON.parse(stored) : [];
    },

    async getStrategies() {
        const data = await this._fetchJSON('/api/strategies');
        if (data) return data;

        return [
            { id: "victory_cinema", name: "Victory Cinema (Custom Scraper Driver)" },
            { id: "generic_selector", name: "Generic Selector / Keyword Matcher" }
        ];
    },

    async simulateAlert(movieTitle, theatre, bookingUrl) {
        const data = await this._fetchJSON('/api/alerts/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ movie_title: movieTitle, theatre, booking_url: bookingUrl })
        });
        if (data) return data;

        // Static fallback simulation
        const alertObj = {
            id: `alert-sim-${Date.now()}`,
            target_id: "simulated",
            movie_title: movieTitle,
            theatre: theatre,
            booking_url: bookingUrl,
            details: "🚨 SIMULATION MODE: Tickets officially released! (Test Trigger)",
            timestamp: new Date().toISOString()
        };

        const alerts = await this.getAlerts();
        alerts.unshift(alertObj);
        localStorage.setItem('mtt_alerts', JSON.stringify(alerts));

        if (window.handleAlertTriggered) {
            window.handleAlertTriggered(alertObj);
        }

        // Send client-side ntfy push if configured
        this.sendNtfyPush(movieTitle, theatre, bookingUrl);

        return { success: true, alert: alertObj };
    },

    async testTwilioCall() {
        const res = await fetch('/api/twilio/test', { method: 'POST' });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Twilio test call failed');
        return data;
    },

    async sendNtfyPush(movieTitle, theatre, bookingUrl) {
        try {
            const settings = await this.getSettings();
            let ntfyTarget = settings.ntfy_url || settings.ntfy_topic;
            if (!ntfyTarget) return;

            ntfyTarget = ntfyTarget.trim();
            const url = ntfyTarget.startsWith('http://') || ntfyTarget.startsWith('https://')
                ? ntfyTarget
                : `https://ntfy.sh/${ntfyTarget.replace(/^\//, '')}`;

            await fetch(url, {
                method: 'POST',
                headers: {
                    'Title': `🎟️ TICKET RELEASE ALERT: ${movieTitle}`,
                    'Priority': 'high',
                    'Tags': 'tickets,clapper,tada',
                    'Click': bookingUrl,
                    'Actions': `view, Book Tickets Now, ${bookingUrl}, clear=true`
                },
                body: `Tickets available at ${theatre}! Book your seats now: ${bookingUrl}`
            });
            console.log(`[ntfy] Push notification sent to ${url}`);
        } catch (e) {
            console.warn(`[ntfy] Client-side push notification failed:`, e);
        }
    },

    connectStream(onEvent) {
        try {
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
                console.warn("SSE stream unavailable (static host mode).", e);
                eventSource.close();
            };
            return eventSource;
        } catch (e) {
            console.warn("EventSource initialization skipped.");
        }
    }
};

window.API = API;

