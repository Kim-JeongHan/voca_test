// IndexedDB wrapper for deck and stats storage
const VocaStorage = (() => {
    const DB_NAME = 'voca_trainer';
    const DB_VERSION = 3;
    const DECK_STORE = 'decks';
    const STATS_STORE = 'stats';
    const WRONG_STORE = 'wrong';
    const SESSION_STORE = 'session';
    const AUDIO_STORE = 'audio';

    let db = null;

    async function init() {
        if (db) {
            console.log('💾 Storage: Already initialized');
            return db;
        }

        console.log('💾 Storage: Initializing IndexedDB...');
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, DB_VERSION);

            request.onerror = () => {
                console.error('💾 Storage: Failed to open DB:', request.error);
                reject(request.error);
            };

            request.onsuccess = () => {
                db = request.result;
                console.log('💾 Storage: IndexedDB initialized successfully');
                resolve(db);
            };

            request.onupgradeneeded = (event) => {
                console.log('💾 Storage: Upgrading DB schema...');
                const database = event.target.result;

                // Deck store: { id, name, words: [{word, meaning}], created }
                if (!database.objectStoreNames.contains(DECK_STORE)) {
                    database.createObjectStore(DECK_STORE, { keyPath: 'id', autoIncrement: true });
                }

                // Stats store: { wordKey, correctCount, wrongCount, lastSeen }
                if (!database.objectStoreNames.contains(STATS_STORE)) {
                    database.createObjectStore(STATS_STORE, { keyPath: 'wordKey' });
                }

                // Wrong list store: { id, word, meaning, timestamp }
                if (!database.objectStoreNames.contains(WRONG_STORE)) {
                    database.createObjectStore(WRONG_STORE, { keyPath: 'id', autoIncrement: true });
                }

                // Session store: { id, deckName, timestamp }
                if (!database.objectStoreNames.contains(SESSION_STORE)) {
                    database.createObjectStore(SESSION_STORE, { keyPath: 'id', autoIncrement: true });
                }

                // Audio cache store (v3): { key, blob, timestamp }
                if (!database.objectStoreNames.contains(AUDIO_STORE)) {
                    const audioStore = database.createObjectStore(AUDIO_STORE, { keyPath: 'key' });
                    audioStore.createIndex('timestamp', 'timestamp');
                }
            };
        });
    }

    async function saveDeck(name, words) {
        console.log(`💾 Storage: Saving deck "${name}" with ${words.length} words...`);
        await init();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(DECK_STORE, 'readwrite');
            const store = tx.objectStore(DECK_STORE);

            // Clear existing decks (single deck mode for now)
            store.clear();

            const deck = {
                name,
                words,
                created: Date.now()
            };
            const request = store.add(deck);
            request.onsuccess = () => {
                console.log(`💾 Storage: Deck "${name}" saved successfully (ID: ${request.result})`);
                resolve(request.result);
            };
            request.onerror = () => {
                console.error('💾 Storage: Failed to save deck:', request.error);
                reject(request.error);
            };
        });
    }

    async function getDeck() {
        console.log('💾 Storage: Getting deck...');
        await init();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(DECK_STORE, 'readonly');
            const store = tx.objectStore(DECK_STORE);
            const request = store.getAll();
            request.onsuccess = () => {
                const decks = request.result;
                const deck = decks.length > 0 ? decks[0] : null;
                console.log('💾 Storage: Got deck:', deck ? `"${deck.name}" (${deck.words.length} words)` : 'null');
                resolve(deck);
            };
            request.onerror = () => {
                console.error('💾 Storage: Failed to get deck:', request.error);
                reject(request.error);
            };
        });
    }

    async function saveWrongList(wrongWords) {
        await init();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(WRONG_STORE, 'readwrite');
            const store = tx.objectStore(WRONG_STORE);

            store.clear();

            wrongWords.forEach(item => {
                store.add({
                    word: item.word,
                    meaning: item.meaning,
                    timestamp: Date.now()
                });
            });

            tx.oncomplete = () => resolve();
            tx.onerror = () => reject(tx.error);
        });
    }

    async function getWrongList() {
        await init();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(WRONG_STORE, 'readonly');
            const store = tx.objectStore(WRONG_STORE);
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async function clearWrongList() {
        await init();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(WRONG_STORE, 'readwrite');
            const store = tx.objectStore(WRONG_STORE);
            const request = store.clear();
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    // Parse CSV text into word pairs
    function parseCSV(csvText) {
        const lines = csvText.split('\n');
        const words = [];

        for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed) continue;

            const commaIdx = trimmed.indexOf(',');
            if (commaIdx === -1) continue;

            const word = trimmed.substring(0, commaIdx).trim();
            const meaning = trimmed.substring(commaIdx + 1).trim();

            if (word && meaning) {
                words.push({ word, meaning });
            }
        }

        return words;
    }

    // Convert word pairs to CSV text
    function toCSV(words) {
        return words.map(w => `${w.word},${w.meaning}`).join('\n');
    }

    // Download text as file
    function downloadFile(filename, content, mimeType = 'text/csv') {
        const blob = new Blob([content], { type: mimeType + ';charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    async function saveSessionState(sessionData) {
        await init();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(SESSION_STORE, 'readwrite');
            const store = tx.objectStore(SESSION_STORE);
            store.clear();
            const request = store.add(sessionData);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    async function getSessionState() {
        await init();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(SESSION_STORE, 'readonly');
            const store = tx.objectStore(SESSION_STORE);
            const request = store.getAll();
            request.onsuccess = () => {
                const sessions = request.result;
                resolve(sessions.length > 0 ? sessions[0] : null);
            };
            request.onerror = () => reject(request.error);
        });
    }

    async function clearSessionState() {
        await init();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(SESSION_STORE, 'readwrite');
            const store = tx.objectStore(SESSION_STORE);
            const request = store.clear();
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    // ==================== Audio Cache Functions ====================

    async function saveAudioBlob(key, blob) {
        await init();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(AUDIO_STORE, 'readwrite');
            const store = tx.objectStore(AUDIO_STORE);
            const request = store.put({
                key,
                blob,
                timestamp: Date.now()
            });
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    async function getAudioBlob(key) {
        await init();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(AUDIO_STORE, 'readonly');
            const store = tx.objectStore(AUDIO_STORE);
            const request = store.get(key);
            request.onsuccess = () => {
                const result = request.result;
                resolve(result ? result.blob : null);
            };
            request.onerror = () => reject(request.error);
        });
    }

    async function clearAudioCache() {
        await init();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(AUDIO_STORE, 'readwrite');
            const store = tx.objectStore(AUDIO_STORE);
            const request = store.clear();
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    async function getAudioCacheStats() {
        await init();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(AUDIO_STORE, 'readonly');
            const store = tx.objectStore(AUDIO_STORE);
            const countReq = store.count();
            countReq.onsuccess = () => {
                resolve({ count: countReq.result });
            };
            countReq.onerror = () => reject(countReq.error);
        });
    }

    async function pruneAudioCache(maxAgeDays = 30) {
        await init();
        const cutoff = Date.now() - (maxAgeDays * 24 * 60 * 60 * 1000);

        return new Promise((resolve, reject) => {
            const tx = db.transaction(AUDIO_STORE, 'readwrite');
            const store = tx.objectStore(AUDIO_STORE);
            const index = store.index('timestamp');
            const range = IDBKeyRange.upperBound(cutoff);

            const request = index.openCursor(range);
            request.onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    cursor.delete();
                    cursor.continue();
                }
            };
            tx.oncomplete = () => resolve();
            tx.onerror = () => reject(tx.error);
        });
    }

    return {
        init,
        saveDeck,
        getDeck,
        saveWrongList,
        getWrongList,
        clearWrongList,
        saveSessionState,
        getSessionState,
        clearSessionState,
        saveAudioBlob,
        getAudioBlob,
        clearAudioCache,
        getAudioCacheStats,
        pruneAudioCache,
        parseCSV,
        toCSV,
        downloadFile
    };
})();
