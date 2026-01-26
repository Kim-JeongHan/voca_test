/**
 * VocaTTS - Text-to-Speech module with caching
 *
 * Features:
 * - Free Dictionary API as primary source (free, accurate pronunciation)
 * - ElevenLabs as fallback (costs money, but works for any text)
 * - IndexedDB caching to minimize API calls
 * - Browser autoplay policy compliance
 */
const VocaTTS = (() => {
    // Configuration
    const CONFIG = {
        // Backend API URL for TTS
        workerUrl: 'https://vocatest-production.up.railway.app/api/v1/tts',
        enabled: true,
        autoPlay: true,
    };

    // State
    let currentAudio = null;
    let audioUnlocked = false; // Browser autoplay policy
    let lastPlayedText = null;

    // ==================== Audio Unlock (Browser Policy) ====================

    /**
     * Call this on user gesture (button click) to unlock audio playback.
     * Required for mobile browsers and TWA.
     */
    function unlockAudio() {
        if (audioUnlocked) return;

        // Create and play a silent audio to unlock
        const silentAudio = new Audio('data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA//tQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAACAAABhgC7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7//////////////////////////////////////////////////////////////////8AAAAATGF2YzU4LjEzAAAAAAAAAAAAAAAAJAAAAAAAAAAAAYYoRwmHAAAAAAD/+9DEAAAIAANIAAAAEYwAbSAAAAETEFNRTMuMTAwVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVU=');
        silentAudio.play().then(() => {
            audioUnlocked = true;
            console.log('TTS: Audio unlocked');
        }).catch(() => {
            // Still mark as unlocked - user gesture occurred
            audioUnlocked = true;
        });
    }

    /**
     * Check if autoplay is allowed (user has interacted)
     */
    function canAutoPlay() {
        return audioUnlocked && CONFIG.enabled && CONFIG.autoPlay;
    }

    // ==================== Audio Fetching ====================

    /**
     * Try to get pronunciation from Free Dictionary API (free, accurate)
     * @param {string} word - English word
     * @returns {Promise<Blob|null>}
     */
    async function fetchFromDictionary(word) {
        try {
            const response = await fetch(
                `https://api.dictionaryapi.dev/api/v2/entries/en/${encodeURIComponent(word)}`,
                { signal: AbortSignal.timeout(5000) }
            );

            if (!response.ok) return null;

            const data = await response.json();
            const phonetics = data[0]?.phonetics || [];

            // Find first phonetic with audio
            for (const phonetic of phonetics) {
                if (phonetic.audio) {
                    const audioResponse = await fetch(phonetic.audio, {
                        signal: AbortSignal.timeout(5000)
                    });
                    if (audioResponse.ok) {
                        return await audioResponse.blob();
                    }
                }
            }
            return null;
        } catch (error) {
            console.warn('Dictionary API error:', error.message);
            return null;
        }
    }

    /**
     * Fetch from ElevenLabs via Cloudflare Worker (costs money)
     * @param {string} text - Text to speak
     * @returns {Promise<Blob|null>}
     */
    async function fetchFromElevenLabs(text) {
        try {
            const response = await fetch(CONFIG.workerUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text }),
                signal: AbortSignal.timeout(10000),
            });

            if (!response.ok) {
                console.warn('ElevenLabs API error:', response.status);
                return null;
            }

            return await response.blob();
        } catch (error) {
            console.warn('ElevenLabs fetch error:', error.message);
            return null;
        }
    }

    /**
     * Get audio blob with caching
     * Priority: Cache > Dictionary API > ElevenLabs
     * @param {string} text - Text to speak
     * @returns {Promise<Blob|null>}
     */
    async function getAudio(text) {
        if (!text) return null;

        const cacheKey = `tts_${text.toLowerCase().trim()}`;

        // 1. Try cache first
        try {
            const cached = await VocaStorage.getAudioBlob(cacheKey);
            if (cached) {
                console.log('TTS: Cache hit for', text);
                return cached;
            }
        } catch (e) {
            console.warn('TTS: Cache read error', e);
        }

        console.log('TTS: Cache miss, fetching', text);

        // 2. Try Dictionary API (free, accurate for English words)
        let blob = await fetchFromDictionary(text);

        // 3. Fallback to ElevenLabs
        if (!blob) {
            blob = await fetchFromElevenLabs(text);
        }

        // 4. Cache the result
        if (blob) {
            try {
                await VocaStorage.saveAudioBlob(cacheKey, blob);
            } catch (e) {
                console.warn('TTS: Cache write error', e);
            }
        }

        return blob;
    }

    // ==================== Playback ====================

    /**
     * Play audio for given text
     * @param {string} text - Text to speak
     * @returns {Promise<boolean>} - Whether playback started
     */
    async function play(text) {
        if (!CONFIG.enabled || !text) return false;

        // Stop any current playback
        stop();

        lastPlayedText = text;

        const blob = await getAudio(text);
        if (!blob) {
            console.warn('TTS: No audio available for', text);
            return false;
        }

        try {
            const url = URL.createObjectURL(blob);
            currentAudio = new Audio(url);

            currentAudio.onended = () => {
                URL.revokeObjectURL(url);
                currentAudio = null;
                updateSpeakerButton(false);
            };

            currentAudio.onerror = () => {
                URL.revokeObjectURL(url);
                currentAudio = null;
                updateSpeakerButton(false);
            };

            updateSpeakerButton(true);
            await currentAudio.play();
            return true;

        } catch (error) {
            console.warn('TTS: Playback error', error.message);
            updateSpeakerButton(false);
            return false;
        }
    }

    /**
     * Stop current playback
     */
    function stop() {
        if (currentAudio) {
            currentAudio.pause();
            currentAudio = null;
            updateSpeakerButton(false);
        }
    }

    /**
     * Replay last played text
     */
    async function replay() {
        if (lastPlayedText) {
            await play(lastPlayedText);
        }
    }

    /**
     * Update speaker button visual state
     */
    function updateSpeakerButton(playing) {
        const btn = document.getElementById('speaker-btn');
        if (btn) {
            btn.classList.toggle('playing', playing);
        }
    }

    // ==================== Settings ====================

    function setEnabled(enabled) {
        CONFIG.enabled = enabled;
        localStorage.setItem('tts_enabled', enabled);
    }

    function isEnabled() {
        return CONFIG.enabled;
    }

    function setAutoPlay(autoPlay) {
        CONFIG.autoPlay = autoPlay;
        localStorage.setItem('tts_autoplay', autoPlay);
    }

    function isAutoPlay() {
        return CONFIG.autoPlay;
    }

    function loadSettings() {
        const enabled = localStorage.getItem('tts_enabled');
        const autoPlay = localStorage.getItem('tts_autoplay');

        if (enabled !== null) CONFIG.enabled = enabled === 'true';
        if (autoPlay !== null) CONFIG.autoPlay = autoPlay === 'true';
    }

    // ==================== Initialization ====================

    loadSettings();

    return {
        // Audio unlock
        unlockAudio,
        canAutoPlay,

        // Playback
        play,
        stop,
        replay,

        // Settings
        setEnabled,
        isEnabled,
        setAutoPlay,
        isAutoPlay,
        loadSettings,
    };
})();
