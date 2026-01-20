// Voca Trainer PWA - Main Application
const VocaApp = (() => {
    // State
    let vocaCore = null;
    let session = null;
    let currentDeck = null;
    let lastWrongCSV = '';
    let focusMode = false;
    let hintCount = 0;
    let currentQuestion = null;
    let currentImageUrl = null; // Current association image URL

    // Available decks (built-in)
    const BUILTIN_DECKS = [
        '1', '2', '4', '5', '6', '12', '13', '14', '15', '16',
        '17', '18', '19', '20', '21', '23', '24', '25', '26', '27',
        '28', '29', '30', '31', '11_12', '123', '456'
    ];

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
        elements.deckSelect = document.getElementById('deck-select');
        elements.importBtn = document.getElementById('import-btn');
        elements.fileInput = document.getElementById('file-input');
        elements.startAllBtn = document.getElementById('start-all-btn');
        elements.startShortBtn = document.getElementById('start-short-btn');
        elements.startWrongBtn = document.getElementById('start-wrong-btn');
        elements.focusModeToggle = document.getElementById('focus-mode-toggle');
        elements.ttsToggle = document.getElementById('tts-toggle');
        elements.ttsAutoPlayToggle = document.getElementById('tts-autoplay-toggle');
        elements.clearAudioCacheBtn = document.getElementById('clear-audio-cache-btn');

        // Session screen
        elements.backBtn = document.getElementById('back-btn');
        elements.progressText = document.getElementById('progress-text');
        elements.progressFill = document.getElementById('progress-fill');
        elements.questionText = document.getElementById('question-text');
        elements.hintText = document.getElementById('hint-text');
        elements.answerInput = document.getElementById('answer-input');
        elements.hintBtn = document.getElementById('hint-btn');
        elements.submitBtn = document.getElementById('submit-btn');
        elements.quitBtn = document.getElementById('quit-btn');
        elements.feedbackArea = document.getElementById('feedback-area');
        elements.feedbackIcon = document.getElementById('feedback-icon');
        elements.feedbackText = document.getElementById('feedback-text');
        elements.attemptInfo = document.getElementById('attempt-info');
        elements.speakerBtn = document.getElementById('speaker-btn');
        elements.associationImage = document.getElementById('association-image');
        elements.imageBtn = document.getElementById('image-btn');

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
        elements.deckSelect.addEventListener('change', handleDeckSelect);
        elements.importBtn.addEventListener('click', () => elements.fileInput.click());
        elements.fileInput.addEventListener('change', handleFileImport);
        elements.startAllBtn.addEventListener('click', () => startSession('all'));
        elements.startShortBtn.addEventListener('click', () => startSession('short'));
        elements.startWrongBtn.addEventListener('click', () => startSession('wrong'));
        elements.focusModeToggle.addEventListener('change', toggleFocusMode);

        // TTS settings
        if (elements.ttsToggle) {
            elements.ttsToggle.checked = VocaTTS.isEnabled();
            elements.ttsToggle.addEventListener('change', (e) => VocaTTS.setEnabled(e.target.checked));
        }
        if (elements.ttsAutoPlayToggle) {
            elements.ttsAutoPlayToggle.checked = VocaTTS.isAutoPlay();
            elements.ttsAutoPlayToggle.addEventListener('change', (e) => VocaTTS.setAutoPlay(e.target.checked));
        }
        if (elements.clearAudioCacheBtn) {
            elements.clearAudioCacheBtn.addEventListener('click', handleClearAudioCache);
        }

        // Session screen
        elements.backBtn.addEventListener('click', confirmQuit);
        elements.answerInput.addEventListener('keydown', handleAnswerKeydown);
        elements.hintBtn.addEventListener('click', handleHintClick);
        elements.submitBtn.addEventListener('click', handleSubmitClick);
        elements.quitBtn.addEventListener('click', saveAndQuit);

        // Summary screen
        elements.exportWrongBtn.addEventListener('click', exportWrongList);
        elements.retryWrongBtn.addEventListener('click', () => startSession('wrong'));
        elements.homeBtn.addEventListener('click', showHome);

        // Speaker button
        if (elements.speakerBtn) {
            elements.speakerBtn.addEventListener('click', handleSpeakerClick);
        }

        // Image button (manual trigger for association image)
        if (elements.imageBtn) {
            elements.imageBtn.addEventListener('click', handleImageClick);
        }

        // Listen for async image ready events
        window.addEventListener('vocaImageReady', handleImageReady);
    }

    async function handleClearAudioCache() {
        if (confirm('Clear all cached audio? This will not delete your word data.')) {
            await VocaStorage.clearAudioCache();
            alert('Audio cache cleared');
        }
    }

    function handleSpeakerClick() {
        if (currentQuestion?.word) {
            VocaTTS.play(currentQuestion.word);
        }
    }

    async function handleImageClick() {
        if (!currentQuestion?.word) return;
        if (!VocaImage.isEnabled()) {
            console.log('Image generation not configured');
            return;
        }

        // Show loading state
        if (elements.imageBtn) {
            elements.imageBtn.disabled = true;
            elements.imageBtn.textContent = '...';
        }

        try {
            // Force generate image (manual trigger ignores wrong count threshold)
            const imageUrl = await VocaImage.requestImage(currentQuestion.word, { forceGenerate: true });
            if (imageUrl) {
                showAssociationImage(imageUrl);
            }
        } finally {
            if (elements.imageBtn) {
                elements.imageBtn.disabled = false;
                elements.imageBtn.textContent = '🖼️';
            }
        }
    }

    function handleImageReady(event) {
        const { word, imageUrl } = event.detail;
        // Only show if still on the same question
        if (currentQuestion?.word?.toLowerCase() === word.toLowerCase()) {
            showAssociationImage(imageUrl);
        }
    }

    function showAssociationImage(url) {
        if (!elements.associationImage) return;

        // Revoke previous URL
        if (currentImageUrl) {
            VocaImage.revokeImageUrl(currentImageUrl);
        }

        currentImageUrl = url;
        elements.associationImage.src = url;
        elements.associationImage.classList.remove('hidden');
    }

    function hideAssociationImage() {
        if (elements.associationImage) {
            elements.associationImage.classList.add('hidden');
            elements.associationImage.src = '';
        }

        if (currentImageUrl) {
            VocaImage.revokeImageUrl(currentImageUrl);
            currentImageUrl = null;
        }
    }

    async function initStorage() {
        await VocaStorage.init();
    }

    async function loadWasm() {
        // Always use JavaScript fallback for now (WASM has issues on GitHub Pages)
        console.log('Using JavaScript fallback');
        vocaCore = createJSFallback();
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
            return s.replace(/[\s'"]/g, '').toLowerCase();
        }

        function checkAnswer(answer, correct) {
            const normAnswer = normalize(answer);
            // Check if answer matches any of the comma-separated meanings
            const meanings = correct.split(',').map(m => normalize(m.trim()));
            return meanings.some(m => m === normAnswer);
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
                return JSON.stringify({
                    question_id: String(current.id),
                    question_text: current.word,
                    direction: 'en_to_kr',
                    attempt: wc + 1,
                    progress: { done: score, total }
                });
            },
            _session_submit: (_, answer) => {
                if (!current) return JSON.stringify({ is_correct: true, next_action: 'show_summary' });

                const key = current.word + '|' + current.correct;
                const isCorrect = checkAnswer(answer, current.correct);

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
        console.log('🔍 Loading deck from storage...');
        currentDeck = await VocaStorage.getDeck();
        console.log('💾 Current deck from storage:', currentDeck ? `${currentDeck.name} (${currentDeck.words.length} words)` : 'null');

        // Auto-load default deck if no deck or empty words (corrupted data fix)
        if (!currentDeck || !currentDeck.words || currentDeck.words.length === 0) {
            console.log('⚠️ No deck or empty words in storage, loading default deck...');
            await loadDefaultDeck();
            currentDeck = await VocaStorage.getDeck();
            console.log('💾 Current deck after default load:', currentDeck ? `${currentDeck.name} (${currentDeck.words.length} words)` : 'still null');
        }

        populateDeckSelect();
    }

    async function loadDefaultDeck() {
        const defaultDeck = '12'; // Day 12 as default (Day 1 has no meanings)
        try {
            console.log('🔄 Attempting to load default deck:', defaultDeck);
            const response = await fetch(`words/${defaultDeck}.csv`);
            console.log('📡 Fetch response status:', response.status, response.ok);

            if (!response.ok) {
                console.warn('❌ Failed to fetch default deck:', response.status, response.statusText);
                return;
            }

            const text = await response.text();
            console.log('📄 CSV text length:', text.length);

            const words = VocaStorage.parseCSV(text);
            console.log('📝 Parsed words count:', words.length);

            if (words.length > 0) {
                await VocaStorage.saveDeck(defaultDeck, words);
                console.log(`✅ Default deck (Day ${defaultDeck}) loaded automatically`);
            }
        } catch (err) {
            console.error('❌ Failed to load default deck:', err);
        }
    }

    function populateDeckSelect() {
        // Clear existing options except the first one
        while (elements.deckSelect.options.length > 1) {
            elements.deckSelect.remove(1);
        }

        // Add built-in decks
        BUILTIN_DECKS.forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = `Day ${name}`;
            elements.deckSelect.appendChild(option);
        });
    }

    async function handleDeckSelect(e) {
        const deckName = e.target.value;
        if (!deckName) return;

        try {
            const response = await fetch(`words/${deckName}.csv`);
            if (!response.ok) throw new Error('Failed to fetch deck');

            const text = await response.text();
            const words = VocaStorage.parseCSV(text);

            if (words.length === 0) {
                alert('No valid word pairs found in deck');
                return;
            }

            await VocaStorage.saveDeck(deckName, words);
            await loadDeck();
            updateUI();
        } catch (err) {
            console.error('Failed to load deck:', err);
            alert('Failed to load deck');
        }
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

        // Unlock audio on session start (user gesture)
        VocaTTS.unlockAudio();

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

    async function showNextPrompt() {
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

        // Reset hint state for new question
        hintCount = 0;
        currentQuestion = {
            word: prompt.question_text,
            correct: findCorrectAnswer(prompt.question_text),
            attempt: prompt.attempt
        };

        // Hide association image for new question
        hideAssociationImage();

        // Update UI
        elements.questionText.textContent = prompt.question_text;
        // Show letter count as default hint
        const correct = currentQuestion.correct || '';
        const letters = correct.replace(/[\s,"']/g, '');
        elements.hintText.textContent = `Hint: ${'_'.repeat(letters.length)} (${letters.length} 글자)`;
        updateAttemptInfo();

        // TTS: Auto-play on new word (if enabled and unlocked)
        if (VocaTTS.canAutoPlay()) {
            VocaTTS.play(prompt.question_text);
        }

        const progress = prompt.progress || { done: 0, total: 0 };
        elements.progressText.textContent = `${progress.done}/${progress.total}`;
        const percentage = progress.total > 0 ? (progress.done / progress.total) * 100 : 0;
        elements.progressFill.style.width = `${percentage}%`;

        // Reset input and buttons
        elements.answerInput.value = '';
        elements.answerInput.className = '';
        elements.feedbackArea.className = 'hidden';
        elements.hintBtn.disabled = false;
        elements.hintBtn.textContent = 'Hint';
        elements.answerInput.focus();

        // Preload association image if this word qualifies
        if (VocaImage.isEnabled()) {
            VocaImage.preloadIfNeeded(prompt.question_text);
        }
    }

    function findCorrectAnswer(word) {
        if (currentDeck && currentDeck.words) {
            const found = currentDeck.words.find(w => w.word === word);
            return found ? found.meaning : '';
        }
        return '';
    }

    function handleAnswerKeydown(e) {
        if (e.key !== 'Enter') return;

        const answer = elements.answerInput.value.trim();
        if (!answer) return;

        submitAnswer(answer);
    }

    function handleSubmitClick() {
        const answer = elements.answerInput.value.trim();
        if (!answer) return;

        submitAnswer(answer);
    }

    function handleHintClick() {
        hintCount++;
        updateAttemptInfo();

        // Generate hint based on hint count
        // Default (hintCount=0): letter count shown on question load
        // hintCount=1: first letter + underscores
        // hintCount>=2: marked as wrong
        if (currentQuestion) {
            const correct = currentQuestion.correct || '';
            const letters = correct.replace(/[\s,"']/g, '');
            let hint = '';

            if (hintCount === 1) {
                hint = `Hint: ${letters[0] || ''}${'_'.repeat(Math.max(0, letters.length - 1))}`;
            } else {
                hint = `Hint: ${letters.substring(0, 2)}${'_'.repeat(Math.max(0, letters.length - 2))}`;
            }

            elements.hintText.textContent = hint;

            // Mark as wrong if hint used twice or more
            if (hintCount >= 2) {
                elements.hintBtn.disabled = true;
                elements.hintBtn.textContent = 'Wrong (2+ hints)';
            }
        }
    }

    function updateAttemptInfo() {
        const attempt = currentQuestion ? (currentQuestion.attempt || 1) : 1;
        elements.attemptInfo.textContent = `Attempt: ${attempt} | Hints: ${hintCount}`;
    }

    async function saveAndQuit() {
        // Save current session state to storage
        if (session && currentDeck) {
            await VocaStorage.saveSessionState({
                deckName: currentDeck.name,
                timestamp: Date.now()
            });
        }

        if (session && vocaCore.ccall) {
            vocaCore.ccall('voca_session_destroy', null, ['number'], [session]);
        }
        session = null;

        alert('Session saved. You can resume later.');
        showHome();
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

            // TTS: Play word pronunciation on wrong answer
            if (VocaTTS.isEnabled() && currentQuestion?.word) {
                setTimeout(() => VocaTTS.play(currentQuestion.word), 300);
            }

            // Record wrong answer and potentially show association image
            if (VocaImage.isEnabled() && currentQuestion?.word) {
                VocaImage.recordWrongAnswer(currentQuestion.word).then(({ wrongCount, imageUrl }) => {
                    // Show cached image immediately if available
                    if (imageUrl) {
                        showAssociationImage(imageUrl);
                    }
                });
            }
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
        }, feedback.is_correct ? 300 : 1500); // Increased delay for wrong to see image
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
