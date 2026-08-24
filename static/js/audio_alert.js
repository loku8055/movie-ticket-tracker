/**
 * Web Audio API & Speech Synthesis helper for immediate high-priority alerts
 */
class AudioAlertService {
    constructor() {
        this.audioCtx = null;
        this.selectedTone = 'chime';
    }

    init() {
        if (!this.audioCtx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            this.audioCtx = new AudioContext();
        }
    }

    playChime() {
        try {
            this.init();
            if (this.audioCtx.state === 'suspended') {
                this.audioCtx.resume();
            }

            const now = this.audioCtx.currentTime;

            // Tone 1: High crisp alert chime
            const osc1 = this.audioCtx.createOscillator();
            const gain1 = this.audioCtx.createGain();
            osc1.type = 'sine';
            osc1.frequency.setValueAtTime(880, now); // A5
            osc1.frequency.exponentialRampToValueAtTime(1760, now + 0.15); // A6
            gain1.gain.setValueAtTime(0.3, now);
            gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
            osc1.connect(gain1);
            gain1.connect(this.audioCtx.destination);
            osc1.start(now);
            osc1.stop(now + 0.6);

            // Tone 2: Success fanfare second chord
            const osc2 = this.audioCtx.createOscillator();
            const gain2 = this.audioCtx.createGain();
            osc2.type = 'triangle';
            osc2.frequency.setValueAtTime(1318.5, now + 0.18); // E6
            gain2.gain.setValueAtTime(0.35, now + 0.18);
            gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.8);
            osc2.connect(gain2);
            gain2.connect(this.audioCtx.destination);
            osc2.start(now + 0.18);
            osc2.stop(now + 0.8);
        } catch (e) {
            console.warn("Web Audio API warning:", e);
        }
    }

    playSiren() {
        try {
            this.init();
            if (this.audioCtx.state === 'suspended') this.audioCtx.resume();
            const now = this.audioCtx.currentTime;

            for (let i = 0; i < 3; i++) {
                const startTime = now + (i * 0.18);
                const osc = this.audioCtx.createOscillator();
                const gain = this.audioCtx.createGain();
                osc.type = 'sawtooth';
                osc.frequency.setValueAtTime(950, startTime);
                osc.frequency.exponentialRampToValueAtTime(450, startTime + 0.12);
                gain.gain.setValueAtTime(0.2, startTime);
                gain.gain.exponentialRampToValueAtTime(0.001, startTime + 0.15);
                osc.connect(gain);
                gain.connect(this.audioCtx.destination);
                osc.start(startTime);
                osc.stop(startTime + 0.15);
            }
        } catch (e) {
            console.warn("Web Audio API warning:", e);
        }
    }

    playSynthwave() {
        try {
            this.init();
            if (this.audioCtx.state === 'suspended') this.audioCtx.resume();
            const now = this.audioCtx.currentTime;

            const osc = this.audioCtx.createOscillator();
            const gain = this.audioCtx.createGain();
            osc.type = 'square';
            osc.frequency.setValueAtTime(220, now);
            osc.frequency.exponentialRampToValueAtTime(880, now + 0.4);
            gain.gain.setValueAtTime(0.25, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.7);
            osc.connect(gain);
            gain.connect(this.audioCtx.destination);
            osc.start(now);
            osc.stop(now + 0.7);
        } catch (e) {
            console.warn("Web Audio API warning:", e);
        }
    }

    playSelectedTone() {
        if (this.selectedTone === 'siren') this.playSiren();
        else if (this.selectedTone === 'synthwave') this.playSynthwave();
        else this.playChime();
    }

    speak(text) {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel(); // Clear queue
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 1.0;
            utterance.pitch = 1.1;
            window.speechSynthesis.speak(utterance);
        }
    }

    triggerAlert(movieTitle, theatre) {
        this.playSelectedTone();
        const alertText = `Attention! Tickets for ${movieTitle} at ${theatre} are now available! Book your seats now!`;
        this.speak(alertText);
    }
}

window.audioAlert = new AudioAlertService();
