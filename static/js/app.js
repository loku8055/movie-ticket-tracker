document.addEventListener('DOMContentLoaded', () => {
    let targetsState = [];
    let settingsState = {};

    // DOM Elements
    const targetsGrid = document.getElementById('targets-grid');
    const terminalLogs = document.getElementById('terminal-logs');
    const alertHistoryList = document.getElementById('alert-history-list');
    const addTargetModal = document.getElementById('add-target-modal');
    const btnAddTarget = document.getElementById('btn-add-target');
    const btnCloseModal = document.getElementById('btn-close-modal');
    const formAddTarget = document.getElementById('form-add-target');
    const strategySelect = document.getElementById('strategy_id');
    const genericFields = document.getElementById('generic-fields');
    
    // Simulation Buttons
    const btnTestSound = document.getElementById('btn-test-sound');
    const btnTestVoice = document.getElementById('btn-test-voice');
    const btnSimulateAlert = document.getElementById('btn-simulate-alert');

    // Settings elements
    const formSettings = document.getElementById('form-settings');

    // Initialize App
    async function init() {
        try {
            settingsState = await API.getSettings();
            targetsState = await API.getTargets();
            const logs = await API.getLogs();
            const alerts = await API.getAlerts();
            const strategies = await API.getStrategies();

            renderTargets(targetsState);
            renderLogs(logs);
            renderAlerts(alerts);
            populateStrategies(strategies);
            populateSettings(settingsState);

            // Connect SSE event stream
            API.connectStream(handleSSEEvent);

        } catch (e) {
            console.error("App initialization failed:", e);
        }
    }

    // SSE Event Handler
    function handleSSEEvent(payload) {
        if (!payload || !payload.event) return;

        if (payload.event === 'log:new') {
            appendLogLine(payload.data);
        } else if (payload.event === 'target:updated') {
            updateTargetInState(payload.data);
        } else if (payload.event === 'alert:triggered') {
            handleAlertTriggered(payload.data);
        }
    }

    function updateTargetInState(updatedTarget) {
        const idx = targetsState.findIndex(t => t.id === updatedTarget.id);
        if (idx !== -1) {
            targetsState[idx] = updatedTarget;
        } else {
            targetsState.push(updatedTarget);
        }
        renderTargets(targetsState);
    }

    function handleAlertTriggered(alertData) {
        // Prepend to alert history
        renderAlertItem(alertData, true);

        // Sound & Voice Alert
        if (settingsState.sound_enabled !== false) {
            window.audioAlert.triggerAlert(alertData.movie_title, alertData.theatre);
        }
    }

    // Render Targets Grid
    function renderTargets(targets) {
        targetsGrid.innerHTML = '';
        if (targets.length === 0) {
            targetsGrid.innerHTML = `<div class="glass-panel" style="padding: 30px; text-align: center; color: var(--text-muted);">No cinema targets monitored. Click "+ Add Cinema Target" to create one.</div>`;
            return;
        }

        targets.forEach(t => {
            const card = document.createElement('div');
            card.className = `glass-panel target-card status-${t.last_status || 'PENDING'}`;
            
            const lastCheckedFormatted = t.last_checked ? new Date(t.last_checked).toLocaleTimeString() : 'Never';
            const bookingUrl = t.booking_url || t.target_url;

            let releaseBannerHTML = '';
            if (t.last_status === 'AVAILABLE') {
                releaseBannerHTML = `
                    <div class="release-banner">
                        <h3>🎉 TICKETS OFFICIALLY RELEASED!</h3>
                        <p>Booking is open at Victory Cinema. Click below to secure your seats instantly!</p>
                        <a href="${bookingUrl}" target="_blank" rel="noopener" class="btn btn-success" style="width: 100%;">
                           🎟️ BOOK TICKETS NOW ON VICTORY CINEMA ⚡
                        </a>
                    </div>
                `;
            }

            card.innerHTML = `
                <div class="card-top">
                    <div class="movie-info">
                        <span class="theatre-badge">📍 ${escapeHTML(t.theatre || 'Cinema')}</span>
                        <h2>${escapeHTML(t.movie_title)}</h2>
                        <div class="strategy-tag">Strategy: ${escapeHTML(t.strategy_id)} • Interval: ${t.interval_sec}s</div>
                    </div>
                    <span class="status-pill ${t.last_status || 'PENDING'}">${t.last_status || 'PENDING'}</span>
                </div>

                ${releaseBannerHTML}

                <div class="card-metrics">
                    <div class="metric-item">
                        <div class="metric-label">Status</div>
                        <div class="metric-value">${t.enabled ? '🟢 Active' : '⏸️ Paused'}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Latency</div>
                        <div class="metric-value">${t.last_latency_ms || 0} ms</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Last Checked</div>
                        <div class="metric-value">${lastCheckedFormatted}</div>
                    </div>
                </div>

                <div class="card-actions">
                    <button class="btn btn-secondary btn-sm" onclick="forceCheck('${t.id}')">🔄 Check Now</button>
                    <button class="btn btn-secondary btn-sm" onclick="toggleTarget('${t.id}')">${t.enabled ? 'Pause' : 'Resume'}</button>
                    <a href="${escapeHTML(t.target_url)}" target="_blank" rel="noopener" class="btn btn-secondary btn-sm">🔗 Page</a>
                    <button class="btn btn-secondary btn-sm" style="color: var(--danger);" onclick="deleteTarget('${t.id}')">🗑️</button>
                </div>
            `;

            targetsGrid.appendChild(card);
        });
    }

    // Log Rendering
    function renderLogs(logs) {
        terminalLogs.innerHTML = '';
        logs.reverse().forEach(log => appendLogLine(log, false));
        terminalLogs.scrollTop = terminalLogs.scrollHeight;
    }

    function appendLogLine(log, autoScroll = true) {
        const timeStr = log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
        const line = document.createElement('div');
        line.className = 'log-line';
        line.innerHTML = `
            <span class="log-time">[${timeStr}]</span>
            <span class="log-target">${escapeHTML(log.movie_title || 'Target')}</span>
            <span class="log-status ${log.status}">${log.status}</span>
            <span class="log-detail">(${log.latency_ms || 0}ms) ${escapeHTML(log.details || '')}</span>
        `;
        terminalLogs.appendChild(line);
        if (autoScroll) {
            terminalLogs.scrollTop = terminalLogs.scrollHeight;
        }
    }

    // Alert History Rendering
    function renderAlerts(alerts) {
        alertHistoryList.innerHTML = '';
        if (alerts.length === 0) {
            alertHistoryList.innerHTML = `<div style="padding: 16px; color: var(--text-muted); font-size: 0.85rem;">No release alerts triggered yet.</div>`;
            return;
        }
        alerts.forEach(a => renderAlertItem(a, false));
    }

    function renderAlertItem(alertData, prepend = true) {
        const timeStr = alertData.timestamp ? new Date(alertData.timestamp).toLocaleString() : new Date().toLocaleString();
        const item = document.createElement('div');
        item.className = 'glass-panel';
        item.style.padding = '14px';
        item.style.marginBottom = '10px';
        item.style.borderLeft = '3px solid var(--success)';

        item.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
                <strong style="color: var(--success); font-size: 0.95rem;">🎟️ ${escapeHTML(alertData.movie_title)}</strong>
                <span style="font-size: 0.75rem; color: var(--text-dim);">${timeStr}</span>
            </div>
            <div style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 8px;">Theatre: ${escapeHTML(alertData.theatre)} • ${escapeHTML(alertData.details || '')}</div>
            <a href="${escapeHTML(alertData.booking_url)}" target="_blank" rel="noopener" class="btn btn-success btn-sm">Direct Booking Link ➔</a>
        `;

        if (prepend && alertHistoryList.firstChild) {
            alertHistoryList.insertBefore(item, alertHistoryList.firstChild);
        } else {
            alertHistoryList.appendChild(item);
        }
    }

    // Global Functions for inline onclick handlers
    window.forceCheck = async (targetId) => {
        try {
            await API.forceCheck(targetId);
        } catch (e) {
            alert("Force check error: " + e.message);
        }
    };

    window.toggleTarget = async (targetId) => {
        try {
            const updated = await API.toggleTarget(targetId);
            updateTargetInState(updated);
        } catch (e) {
            alert("Toggle error: " + e.message);
        }
    };

    window.deleteTarget = async (targetId) => {
        if (confirm("Are you sure you want to remove this monitored cinema target?")) {
            try {
                await API.deleteTarget(targetId);
                targetsState = targetsState.filter(t => t.id !== targetId);
                renderTargets(targetsState);
            } catch (e) {
                alert("Delete error: " + e.message);
            }
        }
    };

    // Populate Modals & Forms
    function populateStrategies(strategies) {
        strategySelect.innerHTML = '';
        strategies.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.id;
            opt.textContent = `${s.name} (${s.id})`;
            strategySelect.appendChild(opt);
        });
    }

    function populateSettings(settings) {
        if (document.getElementById('set_sound_enabled')) {
            document.getElementById('set_sound_enabled').checked = settings.sound_enabled !== false;
            document.getElementById('set_desktop_notifications').checked = settings.desktop_notifications !== false;
            document.getElementById('set_voice_alerts').checked = settings.voice_alerts !== false;
            document.getElementById('set_telegram_webhook_url').value = settings.telegram_webhook_url || '';
            document.getElementById('set_discord_webhook_url').value = settings.discord_webhook_url || '';
            document.getElementById('set_custom_webhook_url').value = settings.custom_webhook_url || '';
        }
    }

    // Event Listeners
    btnAddTarget.addEventListener('click', () => {
        window.audioAlert.init(); // Initialize audio context on click
        addTargetModal.classList.add('active');
    });

    btnCloseModal.addEventListener('click', () => {
        addTargetModal.classList.remove('active');
    });

    strategySelect.addEventListener('change', (e) => {
        if (e.target.value === 'generic_selector') {
            genericFields.style.display = 'block';
        } else {
            genericFields.style.display = 'none';
        }
    });

    formAddTarget.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(formAddTarget);
        const data = {
            movie_title: formData.get('movie_title'),
            theatre: formData.get('theatre'),
            target_url: formData.get('target_url'),
            strategy_id: formData.get('strategy_id'),
            selector: formData.get('selector'),
            keyword: formData.get('keyword'),
            interval_sec: parseInt(formData.get('interval_sec') || 15)
        };

        try {
            const newTarget = await API.addTarget(data);
            updateTargetInState(newTarget);
            formAddTarget.reset();
            addTargetModal.classList.remove('active');
        } catch (err) {
            alert("Error adding target: " + err.message);
        }
    });

    if (formSettings) {
        formSettings.addEventListener('submit', async (e) => {
            e.preventDefault();
            const updatedSettings = {
                sound_enabled: document.getElementById('set_sound_enabled').checked,
                desktop_notifications: document.getElementById('set_desktop_notifications').checked,
                voice_alerts: document.getElementById('set_voice_alerts').checked,
                telegram_webhook_url: document.getElementById('set_telegram_webhook_url').value.trim(),
                discord_webhook_url: document.getElementById('set_discord_webhook_url').value.trim(),
                custom_webhook_url: document.getElementById('set_custom_webhook_url').value.trim()
            };
            settingsState = await API.updateSettings(updatedSettings);
            alert("Settings saved successfully!");
        });
    }

    // Simulation Triggers
    if (btnTestSound) {
        btnTestSound.addEventListener('click', () => {
            window.audioAlert.playChime();
        });
    }

    if (btnTestVoice) {
        btnTestVoice.addEventListener('click', () => {
            window.audioAlert.speak("Testing Movie Ticket Release Tracker voice alert system.");
        });
    }

    if (btnSimulateAlert) {
        btnSimulateAlert.addEventListener('click', async () => {
            try {
                await API.simulateAlert(
                    "Toxic: A Fairy Tale for Grown Ups (Kannada)",
                    "Victory Cinema",
                    "https://victorycinema.in/showing/"
                );
            } catch (err) {
                alert("Simulate error: " + err.message);
            }
        });
    }

    // Helpers
    function escapeHTML(str) {
        if (!str) return '';
        return str.replace(/[&<>'"]/g, 
            tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
        );
    }

    init();
});
