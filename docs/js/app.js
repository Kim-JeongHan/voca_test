// Voca Trainer PWA - Main Application
const VocaApp = (() => {
    // State
    let vocaCore = null;
    let session = null;
    let currentDeck = null;
    let lastWrongCSV = '';
    let focusMode = false;

    // DOM Elements
    const elements = {};

    // Initialize application
    async function init() {
        cacheElements();
        bindEvents();
        await initStorage();
        await loadWasm();
        await loadDeck();
        updateUI();
    }

    function cacheElements() {
        // Screens
        elements.homeScreen = document.getElementById('home-screen');
        elements.sessionScreen = document.getElementById('session-screen');
        elements.summaryScreen = document.getElementById('summary-screen');

        // Home screen
        elements.deckName = document.getElementById('deck-name');
        elements.deckCount = document.getElementById('deck-count');
        elements.importBtn = document.getElementById('import-btn');
        elements.fileInput = document.getElementById('file-input');
        elements.startAllBtn = document.getElementById('start-all-btn');
        elements.startShortBtn = document.getElementById('start-short-btn');
        elements.startWrongBtn = document.getElementById('start-wrong-btn');
        elements.focusModeToggle = document.getElementById('focus-mode-toggle');

        // Session screen
        elements.backBtn = document.getElementById('back-btn');
        elements.progressText = document.getElementById('progress-text');
        elements.progressFill = document.getElementById('progress-fill');
        elements.questionText = document.getElementById('question-text');
        elements.hintText = document.getElementById('hint-text');
        elements.answerInput = document.getElementById('answer-input');
        elements.feedbackArea = document.getElementById('feedback-area');
        elements.feedbackIcon = document.getElementById('feedback-icon');
        elements.feedbackText = document.getElementById('feedback-text');
        elements.attemptInfo = document.getElementById('attempt-info');

        // Summary screen
        elements.scoreValue = document.getElementById('score-value');
        elements.scoreTotal = document.getElementById('score-total');
        elements.wrongCount = document.getElementById('wrong-count');
        elements.exportWrongBtn = document.getElementById('export-wrong-btn');
        elements.retryWrongBtn = document.getElementById('retry-wrong-btn');
        elements.homeBtn = document.getElementById('home-btn');
    }

    function bindEvents() {
        // Home screen
        elements.importBtn.addEventListener('click', () => elements.fileInput.click());
        elements.fileInput.addEventListener('change', handleFileImport);
        elements.startAllBtn.addEventListener('click', () => startSession('all'));
        elements.startShortBtn.addEventListener('click', () => startSession('short'));
        elements.startWrongBtn.addEventListener('click', () => startSession('wrong'));
        elements.focusModeToggle.addEventListener('change', toggleFocusMode);

        // Session screen
        elements.backBtn.addEventListener('click', confirmQuit);
        elements.answerInput.addEventListener('keydown', handleAnswerKeydown);

        // Summary screen
        elements.exportWrongBtn.addEventListener('click', exportWrongList);
        elements.retryWrongBtn.addEventListener('click', () => startSession('wrong'));
        elements.homeBtn.addEventListener('click', showHome);
    }

    async function initStorage() {
        await VocaStorage.init();
    }

    async function loadWasm() {
        try {
            // Check if WASM module exists
            if (typeof createVocaCore === 'function') {
                vocaCore = await createVocaCore();
                console.log('WASM module loaded');
            } else {
                console.warn('WASM module not available, using JavaScript fallback');
                vocaCore = createJSFallback();
            }
        } catch (err) {
            console.error('Failed to load WASM:', err);
            vocaCore = createJSFallback();
        }
    }

    // JavaScript fallback when WASM is not available
    function createJSFallback() {
        let words = [];
        let queue = [];
        let retryQueue = [];
        let current = null;
        let score = 0;
        let total = 0;
        let wrongList = [];
        let wrongCounts = {};

        function normalize(s) {
            return s.replace(/[\s,'"]/g, '').toLowerCase();
        }

        return {
            _session_create: () => ({}),
            _session_destroy: () => {},
            _session_load_csv: (_, csv) => {
                words = VocaStorage.parseCSV(csv);
                return words.length;
            },
            _session_start: () => {
                queue = words.map((_, i) => i);
                retryQueue = [];
                current = null;
                score = 0;
                total = queue.length;
                wrongList = [];
                wrongCounts = {};
            },
            _session_start_indices: (_, indices) => {
                const idxArr = indices.split(',').map(Number).filter(i => i >= 0 && i < words.length);
                queue = idxArr;
                retryQueue = [];
                current = null;
                score = 0;
                total = queue.length;
                wrongList = [];
                wrongCounts = {};
            },
            _session_get_prompt: () => {
                if (!current) {
                    if (retryQueue.length > 0) {
                        current = { ...retryQueue.shift(), fromRetry: true };
                    } else if (queue.length > 0) {
                        const idx = queue.shift();
                        current = { word: words[idx].word, correct: words[idx].meaning, id: idx, fromRetry: false };
                    } else {
                        return JSON.stringify({ score, total, wrong_count: wrongList.length });
                    }
                }
                const key = current.word + '|' + current.correct;
                const wc = wrongCounts[key] || 0;
                let hint = '';
                if (wc > 0) {
                    const letters = current.correct.replace(/[\s,]/g, '');
                    if (wc === 1) hint = `Hint: ${'_'.repeat(letters.length)} (${letters.length} 글자)`;
                    else if (wc === 2) hint = `Hint: ${letters[0]}${'_'.repeat(letters.length - 1)}`;
                    else if (wc === 3) hint = `Hint: ${letters.substring(0, 2)}${'_'.repeat(letters.length - 2)}`;
                    else hint = `Hint: ${current.correct} (type it again)`;
                }
                return JSON.stringify({
                    question_id: String(current.id),
                    question_text: current.word,
                    direction: 'en_to_kr',
                    hint,
                    attempt: wc + 1,
                    progress: { done: score, total }
                });
            },
            _session_submit: (_, answer) => {
                if (!current) return JSON.stringify({ is_correct: true, next_action: 'show_summary' });

                const key = current.word + '|' + current.correct;
                const isCorrect = normalize(answer) === normalize(current.correct);

                if (!isCorrect) {
                    wrongCounts[key] = (wrongCounts[key] || 0) + 1;
                    if (!wrongList.find(w => w.word === current.word)) {
                        wrongList.push({ word: current.word, meaning: current.correct });
                    }
                    retryQueue.push(current);
                    const c = current;
                    current = null;
                    return JSON.stringify({
                        is_correct: false,
                        correct_answer: c.correct,
                        next_action: 'retry_same',
                        hint_level: wrongCounts[key]
                    });
                }

                if (!current.fromRetry) score++;
                const next = (queue.length === 0 && retryQueue.length === 0) ? 'show_summary' : 'next_question';
                current = null;
                return JSON.stringify({
                    is_correct: true,
                    correct_answer: current ? current.correct : '',
                    next_action: next,
                    hint_level: wrongCounts[key] || 0
                });
            },
            _session_summary: () => JSON.stringify({ score, total, wrong_count: wrongList.length }),
            _session_export_wrong: () => wrongList.map(w => `${w.word},${w.meaning}`).join('\n'),
            _session_is_finished: () => (queue.length === 0 && retryQueue.length === 0 && !current) ? 1 : 0,
            _free_string: () => {},
            _malloc: () => 0,
            _free: () => {},
            UTF8ToString: (ptr) => ptr,
            stringToUTF8: (str, ptr, len) => str,
            lengthBytesUTF8: (str) => str.length
        };
    }

    async function loadDeck() {
        currentDeck = await VocaStorage.getDeck();
    }

    function updateUI() {
        if (currentDeck) {
            elements.deckName.textContent = currentDeck.name;
            elements.deckCount.textContent = `${currentDeck.words.length} words`;
            elements.startAllBtn.disabled = false;
            elements.startShortBtn.disabled = currentDeck.words.length < 10;
        } else {
            elements.deckName.textContent = 'No deck loaded';
            elements.deckCount.textContent = '0 words';
            elements.startAllBtn.disabled = true;
            elements.startShortBtn.disabled = true;
        }

        updateWrongButton();
    }

    async function updateWrongButton() {
        const wrongList = await VocaStorage.getWrongList();
        elements.startWrongBtn.disabled = wrongList.length === 0;
        elements.retryWrongBtn.disabled = wrongList.length === 0;
    }

    async function handleFileImport(e) {
        const file = e.target.files[0];
        if (!file) return;

        try {
            const text = await file.text();
            const words = VocaStorage.parseCSV(text);

            if (words.length === 0) {
                alert('No valid word pairs found in CSV');
                return;
            }

            const name = file.name.replace(/\.csv$/i, '');
            await VocaStorage.saveDeck(name, words);
            await loadDeck();
            updateUI();
        } catch (err) {
            console.error('Import failed:', err);
            alert('Failed to import CSV file');
        }

        elements.fileInput.value = '';
    }

    async function startSession(mode) {
        if (!currentDeck) return;

        // Create WASM session
        if (vocaCore._session_create) {
            session = vocaCore._session_create();
        }

        // Load words
        const csv = VocaStorage.toCSV(currentDeck.words);
        if (vocaCore.ccall) {
            vocaCore.ccall('voca_session_load_csv', 'number', ['number', 'string'], [session, csv]);
        } else {
            vocaCore._session_load_csv(session, csv);
        }

        // Start with appropriate indices
        if (mode === 'all') {
            if (vocaCore.ccall) {
                vocaCore.ccall('voca_session_start', null, ['number'], [session]);
            } else {
                vocaCore._session_start(session);
            }
        } else if (mode === 'short') {
            const count = Math.min(20, currentDeck.words.length);
            const shuffled = [...Array(currentDeck.words.length).keys()].sort(() => Math.random() - 0.5);
            const indices = shuffled.slice(0, count).join(',');
            if (vocaCore.ccall) {
                vocaCore.ccall('voca_session_start_indices', null, ['number', 'string'], [session, indices]);
            } else {
                vocaCore._session_start_indices(session, indices);
            }
        } else if (mode === 'wrong') {
            const wrongList = await VocaStorage.getWrongList();
            const indices = [];
            wrongList.forEach(w => {
                const idx = currentDeck.words.findIndex(dw => dw.word === w.word && dw.meaning === w.meaning);
                if (idx >= 0) indices.push(idx);
            });
            if (indices.length === 0) return;

            if (vocaCore.ccall) {
                vocaCore.ccall('voca_session_start_indices', null, ['number', 'string'], [session, indices.join(',')]);
            } else {
                vocaCore._session_start_indices(session, indices.join(','));
            }
            await VocaStorage.clearWrongList();
        }

        showScreen('session');
        showNextPrompt();
    }

    function showNextPrompt() {
        let promptJson;
        if (vocaCore.ccall) {
            const ptr = vocaCore.ccall('voca_session_get_prompt', 'number', ['number'], [session]);
            promptJson = vocaCore.UTF8ToString(ptr);
            vocaCore.ccall('voca_free_string', null, ['number'], [ptr]);
        } else {
            promptJson = vocaCore._session_get_prompt(session);
        }

        const prompt = JSON.parse(promptJson);

        // Check if session finished
        if (prompt.score !== undefined) {
            showSummary(prompt);
            return;
        }

        // Update UI
        elements.questionText.textContent = prompt.question_text;
        elements.hintText.textContent = prompt.hint || '';
        elements.attemptInfo.textContent = `Attempt: ${prompt.attempt}`;

        const progress = prompt.progress;
        elements.progressText.textContent = `${progress.done}/${progress.total}`;
        elements.progressFill.style.width = `${(progress.done / progress.total) * 100}%`;

        // Reset input
        elements.answerInput.value = '';
        elements.answerInput.className = '';
        elements.feedbackArea.className = 'hidden';
        elements.answerInput.focus();
    }

    function handleAnswerKeydown(e) {
        if (e.key !== 'Enter') return;

        const answer = elements.answerInput.value.trim();
        if (!answer) return;

        submitAnswer(answer);
    }

    async function submitAnswer(answer) {
        let feedbackJson;
        if (vocaCore.ccall) {
            const ptr = vocaCore.ccall('voca_session_submit', 'number', ['number', 'string'], [session, answer]);
            feedbackJson = vocaCore.UTF8ToString(ptr);
            vocaCore.ccall('voca_free_string', null, ['number'], [ptr]);
        } else {
            feedbackJson = vocaCore._session_submit(session, answer);
        }

        const feedback = JSON.parse(feedbackJson);

        // Show feedback
        if (feedback.is_correct) {
            elements.answerInput.classList.add('correct');
            elements.feedbackArea.className = 'correct';
            elements.feedbackIcon.textContent = '✓';
            elements.feedbackText.textContent = 'Correct!';
        } else {
            elements.answerInput.classList.add('incorrect');
            elements.feedbackArea.className = 'incorrect';
            elements.feedbackIcon.textContent = '✗';
            elements.feedbackText.textContent = feedback.correct_answer;
        }

        // Handle next action
        setTimeout(() => {
            if (feedback.next_action === 'show_summary') {
                let summaryJson;
                if (vocaCore.ccall) {
                    const ptr = vocaCore.ccall('voca_session_summary', 'number', ['number'], [session]);
                    summaryJson = vocaCore.UTF8ToString(ptr);
                    vocaCore.ccall('voca_free_string', null, ['number'], [ptr]);
                } else {
                    summaryJson = vocaCore._session_summary(session);
                }
                showSummary(JSON.parse(summaryJson));
            } else {
                showNextPrompt();
            }
        }, feedback.is_correct ? 300 : 1000);
    }

    async function showSummary(summary) {
        elements.scoreValue.textContent = summary.score;
        elements.scoreTotal.textContent = `/${summary.total}`;
        elements.wrongCount.textContent = summary.wrong_count;

        // Get and save wrong list
        if (vocaCore.ccall) {
            const ptr = vocaCore.ccall('voca_session_export_wrong', 'number', ['number'], [session]);
            lastWrongCSV = vocaCore.UTF8ToString(ptr);
            vocaCore.ccall('voca_free_string', null, ['number'], [ptr]);
        } else {
            lastWrongCSV = vocaCore._session_export_wrong(session);
        }

        if (lastWrongCSV) {
            const wrongWords = VocaStorage.parseCSV(lastWrongCSV);
            await VocaStorage.saveWrongList(wrongWords);
        }

        await updateWrongButton();
        showScreen('summary');

        // Cleanup session
        if (vocaCore.ccall) {
            vocaCore.ccall('voca_session_destroy', null, ['number'], [session]);
        } else {
            vocaCore._session_destroy(session);
        }
        session = null;
    }

    function exportWrongList() {
        if (!lastWrongCSV) return;
        const filename = `wrong_${new Date().toISOString().slice(0, 10)}.csv`;
        VocaStorage.downloadFile(filename, lastWrongCSV);
    }

    function confirmQuit() {
        if (confirm('Quit session? Progress will be lost.')) {
            if (session && vocaCore.ccall) {
                vocaCore.ccall('voca_session_destroy', null, ['number'], [session]);
            }
            session = null;
            showHome();
        }
    }

    function showHome() {
        showScreen('home');
        updateUI();
    }

    function showScreen(name) {
        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
        document.getElementById(`${name}-screen`).classList.add('active');

        if (name === 'session') {
            elements.answerInput.focus();
        }
    }

    function toggleFocusMode(e) {
        focusMode = e.target.checked;
        document.body.classList.toggle('focus-mode', focusMode);
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    return { init };
})();
