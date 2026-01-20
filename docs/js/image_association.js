// Association Image Module for Vocabulary Learning
// Generates and caches association images using HuggingFace Stable Diffusion API
// Automatically commits generated images to GitHub for persistence

const VocaImage = (() => {
    // Configuration
    const CONFIG = {
        // Cloudflare Worker URL for image generation
        workerUrl: 'https://voca-image-proxy.kimjh9813.workers.dev',

        // Cloudflare Worker URL for GitHub commits
        githubWorkerUrl: 'https://voca-github-proxy.kimjh9813.workers.dev',

        // GitHub raw URL base for checking existing images
        githubRawBase: 'https://raw.githubusercontent.com/kim-jeonghan/voca_test/master/docs/images',

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
     * Set the Worker URLs
     */
    function setWorkerUrl(url) {
        CONFIG.workerUrl = url;
        console.log(`🖼️ Image: Worker URL set to ${url}`);
    }

    function setGithubWorkerUrl(url) {
        CONFIG.githubWorkerUrl = url;
        console.log(`🖼️ Image: GitHub Worker URL set to ${url}`);
    }

    /**
     * Normalize word for file naming
     */
    function normalizeWord(word) {
        return word.toLowerCase().trim().replace(/[^a-z0-9-]/g, '_');
    }

    /**
     * Check if image exists on GitHub
     */
    async function checkGitHubImage(word) {
        const normalized = normalizeWord(word);
        const url = `${CONFIG.githubRawBase}/${normalized}.png`;

        try {
            const response = await fetch(url, { method: 'HEAD' });
            if (response.ok) {
                console.log(`🖼️ Image: Found on GitHub for "${word}"`);
                return url;
            }
        } catch (e) {
            // Image doesn't exist on GitHub
        }
        return null;
    }

    /**
     * Check if a word should have an image generated
     * @param {string} word - The English word
     * @returns {Promise<boolean>}
     */
    async function shouldGenerateImage(word) {
        if (!isEnabled()) return false;

        // Check if image already exists in local cache
        const hasExisting = await VocaStorage.hasImage(word);
        if (hasExisting) return false;

        // Check if image exists on GitHub
        const githubUrl = await checkGitHubImage(word);
        if (githubUrl) return false;

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
     * @returns {Promise<string|null>} - URL for the image, or null on failure
     */
    async function requestImage(word, options = {}) {
        const normalizedWord = word.toLowerCase().trim();

        // Check local cache first
        const cached = await VocaStorage.getImageBlob(normalizedWord);
        if (cached) {
            console.log(`🖼️ Image: Local cache hit for "${normalizedWord}"`);
            return URL.createObjectURL(cached);
        }

        // Check GitHub for existing image
        const githubUrl = await checkGitHubImage(normalizedWord);
        if (githubUrl) {
            // Download and cache locally for offline use
            try {
                const response = await fetch(githubUrl);
                if (response.ok) {
                    const blob = await response.blob();
                    await VocaStorage.saveImageBlob(normalizedWord, blob);
                    return URL.createObjectURL(blob);
                }
            } catch (e) {
                // Return GitHub URL directly if download fails
                return githubUrl;
            }
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

            // Save to local cache
            await VocaStorage.saveImageBlob(word, blob);
            console.log(`🖼️ Image: Generated and cached locally for "${word}"`);

            // Commit to GitHub in background (don't block)
            commitToGitHub(word, blob);

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
     * Commit image to GitHub via Worker
     * @param {string} word - The word
     * @param {Blob} blob - The image blob
     */
    async function commitToGitHub(word, blob) {
        if (!CONFIG.githubWorkerUrl) {
            console.log('🖼️ Image: GitHub worker not configured, skipping commit');
            return;
        }

        try {
            // Convert blob to base64
            const arrayBuffer = await blob.arrayBuffer();
            const base64 = btoa(
                new Uint8Array(arrayBuffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
            );

            const response = await fetch(CONFIG.githubWorkerUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    word: word,
                    imageBase64: base64,
                }),
            });

            if (response.ok) {
                const result = await response.json();
                console.log(`🖼️ Image: Committed to GitHub: ${result.path}`);
            } else {
                const error = await response.json().catch(() => ({}));
                console.warn(`🖼️ Image: GitHub commit failed - ${error.error || response.statusText}`);
            }
        } catch (error) {
            console.warn('🖼️ Image: GitHub commit error:', error);
        }
    }

    /**
     * Get cached image URL for a word (if exists)
     * @param {string} word - The English word
     * @returns {Promise<string|null>} - Object URL or null
     */
    async function getCachedImage(word) {
        const normalizedWord = word.toLowerCase().trim();

        // Check local cache first
        const blob = await VocaStorage.getImageBlob(normalizedWord);
        if (blob) {
            return URL.createObjectURL(blob);
        }

        // Check GitHub
        const githubUrl = await checkGitHubImage(normalizedWord);
        return githubUrl;
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
            // Check local cache first
            const cached = await VocaStorage.getImageBlob(normalizedWord);
            if (cached) {
                imageUrl = URL.createObjectURL(cached);
            } else {
                // Check GitHub
                const githubUrl = await checkGitHubImage(normalizedWord);
                if (githubUrl) {
                    imageUrl = githubUrl;
                    // Cache locally in background
                    fetch(githubUrl).then(r => r.blob()).then(blob => {
                        VocaStorage.saveImageBlob(normalizedWord, blob);
                    }).catch(() => {});
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

        // Check if already cached locally
        const cached = await VocaStorage.hasImage(normalizedWord);
        if (cached) return;

        // Check if on GitHub and cache it
        const githubUrl = await checkGitHubImage(normalizedWord);
        if (githubUrl) {
            try {
                const response = await fetch(githubUrl);
                if (response.ok) {
                    const blob = await response.blob();
                    await VocaStorage.saveImageBlob(normalizedWord, blob);
                }
            } catch (e) {
                // Ignore errors
            }
            return;
        }

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
        setGithubWorkerUrl,
        requestImage,
        getCachedImage,
        recordWrongAnswer,
        preloadIfNeeded,
        getCacheStats,
        clearCache,
        revokeImageUrl,
        shouldGenerateImage,
        checkGitHubImage,
    };
})();
