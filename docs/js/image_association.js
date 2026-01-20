// Association Image Module for Vocabulary Learning
// Generates and caches association images using HuggingFace Stable Diffusion API

const VocaImage = (() => {
    // Configuration
    const CONFIG = {
        // Cloudflare Worker URL - UPDATE THIS after deploying the worker
        workerUrl: '', // e.g., 'https://voca-image-proxy.your-subdomain.workers.dev'

        // Minimum wrong count before generating image
        minWrongCount: 2,

        // Request timeout in ms
        timeout: 35000,

        // Retry settings for model loading
        maxRetries: 3,
        retryDelay: 5000,
    };

    // State
    let pendingRequests = new Map(); // word -> Promise (prevent duplicate requests)
    let enabled = true;

    /**
     * Check if image generation is enabled and configured
     */
    function isEnabled() {
        return enabled && CONFIG.workerUrl !== '';
    }

    /**
     * Enable/disable image generation
     */
    function setEnabled(value) {
        enabled = value;
        console.log(`🖼️ Image: ${enabled ? 'enabled' : 'disabled'}`);
    }

    /**
     * Set the Worker URL
     */
    function setWorkerUrl(url) {
        CONFIG.workerUrl = url;
        console.log(`🖼️ Image: Worker URL set to ${url}`);
    }

    /**
     * Check if a word should have an image generated
     * @param {string} word - The English word
     * @returns {Promise<boolean>}
     */
    async function shouldGenerateImage(word) {
        if (!isEnabled()) return false;

        // Check if image already exists
        const hasExisting = await VocaStorage.hasImage(word);
        if (hasExisting) return false;

        // Check wrong count
        const wrongCount = await VocaStorage.getWrongCount(word);
        return wrongCount >= CONFIG.minWrongCount;
    }

    /**
     * Request an association image for a word
     * Returns cached image if available, otherwise generates new one
     *
     * @param {string} word - The English word
     * @param {object} options - Options
     * @param {boolean} options.forceGenerate - Force generation even if wrong count < threshold
     * @returns {Promise<string|null>} - Object URL for the image, or null on failure
     */
    async function requestImage(word, options = {}) {
        const normalizedWord = word.toLowerCase().trim();

        // Check cache first
        const cached = await VocaStorage.getImageBlob(normalizedWord);
        if (cached) {
            console.log(`🖼️ Image: Cache hit for "${normalizedWord}"`);
            return URL.createObjectURL(cached);
        }

        // Check if we should generate
        if (!options.forceGenerate) {
            const shouldGenerate = await shouldGenerateImage(normalizedWord);
            if (!shouldGenerate) {
                console.log(`🖼️ Image: Skip generation for "${normalizedWord}" (wrong count < ${CONFIG.minWrongCount})`);
                return null;
            }
        }

        // Check if already pending
        if (pendingRequests.has(normalizedWord)) {
            console.log(`🖼️ Image: Waiting for pending request for "${normalizedWord}"`);
            return pendingRequests.get(normalizedWord);
        }

        // Start new request
        const requestPromise = generateImage(normalizedWord);
        pendingRequests.set(normalizedWord, requestPromise);

        try {
            const result = await requestPromise;
            return result;
        } finally {
            pendingRequests.delete(normalizedWord);
        }
    }

    /**
     * Generate a new association image via Cloudflare Worker
     * @param {string} word - The normalized word
     * @returns {Promise<string|null>} - Object URL or null
     */
    async function generateImage(word, retryCount = 0) {
        if (!isEnabled()) {
            console.warn('🖼️ Image: Not configured (workerUrl is empty)');
            return null;
        }

        console.log(`🖼️ Image: Generating image for "${word}" (attempt ${retryCount + 1})`);

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), CONFIG.timeout);

            const response = await fetch(CONFIG.workerUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ word }),
                signal: controller.signal,
            });

            clearTimeout(timeoutId);

            // Handle model loading response
            if (response.status === 503) {
                const data = await response.json();
                if (data.retry && retryCount < CONFIG.maxRetries) {
                    const waitTime = (data.estimated_time || 5) * 1000;
                    console.log(`🖼️ Image: Model loading, retrying in ${waitTime/1000}s...`);
                    await delay(Math.min(waitTime, CONFIG.retryDelay));
                    return generateImage(word, retryCount + 1);
                }
                console.warn('🖼️ Image: Model loading timeout');
                return null;
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                console.warn(`🖼️ Image: Generation failed - ${errorData.error || response.statusText}`);
                return null;
            }

            // Get image blob
            const blob = await response.blob();

            // Save to cache
            await VocaStorage.saveImageBlob(word, blob);
            console.log(`🖼️ Image: Generated and cached for "${word}"`);

            // Return object URL
            return URL.createObjectURL(blob);

        } catch (error) {
            if (error.name === 'AbortError') {
                console.warn(`🖼️ Image: Request timeout for "${word}"`);
            } else {
                console.error(`🖼️ Image: Error generating image for "${word}":`, error);
            }
            return null;
        }
    }

    /**
     * Get cached image URL for a word (if exists)
     * @param {string} word - The English word
     * @returns {Promise<string|null>} - Object URL or null
     */
    async function getCachedImage(word) {
        const normalizedWord = word.toLowerCase().trim();
        const blob = await VocaStorage.getImageBlob(normalizedWord);
        if (blob) {
            return URL.createObjectURL(blob);
        }
        return null;
    }

    /**
     * Record a wrong answer and potentially trigger image generation
     * @param {string} word - The English word
     * @returns {Promise<{wrongCount: number, imageUrl: string|null}>}
     */
    async function recordWrongAnswer(word) {
        const normalizedWord = word.toLowerCase().trim();

        // Increment wrong count
        const wrongCount = await VocaStorage.incrementWrongCount(normalizedWord);
        console.log(`🖼️ Image: Wrong count for "${normalizedWord}" is now ${wrongCount}`);

        // Check if we should generate image
        let imageUrl = null;
        if (wrongCount >= CONFIG.minWrongCount) {
            // Check if already cached
            const cached = await VocaStorage.getImageBlob(normalizedWord);
            if (cached) {
                imageUrl = URL.createObjectURL(cached);
            } else {
                // Generate in background (don't await to not block UI)
                generateImage(normalizedWord).then(url => {
                    if (url) {
                        // Notify that image is ready (dispatch custom event)
                        window.dispatchEvent(new CustomEvent('vocaImageReady', {
                            detail: { word: normalizedWord, imageUrl: url }
                        }));
                    }
                });
            }
        }

        return { wrongCount, imageUrl };
    }

    /**
     * Preload image for a word if it qualifies
     * @param {string} word - The English word
     */
    async function preloadIfNeeded(word) {
        const normalizedWord = word.toLowerCase().trim();

        // Check wrong count
        const wrongCount = await VocaStorage.getWrongCount(normalizedWord);
        if (wrongCount < CONFIG.minWrongCount) return;

        // Check if already cached
        const cached = await VocaStorage.hasImage(normalizedWord);
        if (cached) return;

        // Generate in background
        generateImage(normalizedWord);
    }

    /**
     * Get statistics about the image cache
     * @returns {Promise<{count: number}>}
     */
    async function getCacheStats() {
        return VocaStorage.getImageCacheStats();
    }

    /**
     * Clear the image cache
     */
    async function clearCache() {
        await VocaStorage.clearImageCache();
        console.log('🖼️ Image: Cache cleared');
    }

    /**
     * Utility: delay for ms
     */
    function delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Revoke an object URL when no longer needed
     */
    function revokeImageUrl(url) {
        if (url && url.startsWith('blob:')) {
            URL.revokeObjectURL(url);
        }
    }

    // Public API
    return {
        isEnabled,
        setEnabled,
        setWorkerUrl,
        requestImage,
        getCachedImage,
        recordWrongAnswer,
        preloadIfNeeded,
        getCacheStats,
        clearCache,
        revokeImageUrl,
        shouldGenerateImage,
    };
})();
