// IndexedDB wrapper for deck and stats storage
const VocaStorage = (() => {
    const DB_NAME = 'voca_trainer';
    const DB_VERSION = 1;
    const DECK_STORE = 'decks';
    const STATS_STORE = 'stats';
    const WRONG_STORE = 'wrong';

    let db = null;

    async function init() {
        if (db) return db;

        return new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, DB_VERSION);

            request.onerror = () => reject(request.error);

            request.onsuccess = () => {
                db = request.result;
                resolve(db);
            };

            request.onupgradeneeded = (event) => {
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
            };
        });
    }

    async function saveDeck(name, words) {
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
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async function getDeck() {
        await init();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(DECK_STORE, 'readonly');
            const store = tx.objectStore(DECK_STORE);
            const request = store.getAll();
            request.onsuccess = () => {
                const decks = request.result;
                resolve(decks.length > 0 ? decks[0] : null);
            };
            request.onerror = () => reject(request.error);
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

    return {
        init,
        saveDeck,
        getDeck,
        saveWrongList,
        getWrongList,
        clearWrongList,
        parseCSV,
        toCSV,
        downloadFile
    };
})();
