document.addEventListener("DOMContentLoaded", () => {
    const recordBtn = document.getElementById("recordBtn");
    const sourceLanguageEl = document.getElementById("sourceLanguage");
    const targetLanguageEl = document.getElementById("targetLanguage");
    const originalTextEl = document.getElementById("originalText");
    const translatedTextEl = document.getElementById("translatedText");
    const statusEl = document.getElementById("status");
    const playBtn = document.getElementById("playBtn");
    const swapBtn = document.getElementById("swapBtn");
    const autoPlayToggle = document.getElementById("autoPlayToggle");

    let isRecording = false;
    let recognizer;

    // --- Event Listeners ---
    recordBtn.addEventListener("click", () => {
        isRecording ? stopRecognition() : startRecognition();
    });

    playBtn.addEventListener("click", () => {
        synthesizeAndPlay(translatedTextEl.value, targetLanguageEl.value);
    });

    swapBtn.addEventListener("click", swapLanguages);

    // --- Core Functions ---
    function swapLanguages() {
        const sourceVal = sourceLanguageEl.value;
        const targetVal = targetLanguageEl.value;
        
        const newSourceVal = findBestSourceMatch(targetVal);
        const newTargetVal = findBestTargetMatch(sourceVal);

        if (newSourceVal) {
            sourceLanguageEl.value = newSourceVal;
        }
        if (newTargetVal) {
            targetLanguageEl.value = newTargetVal;
        }
    }

    function findBestSourceMatch(targetCode) {
        // Example: target 'es' should map to a source like 'es-ES'
        // Find the most common variant first, then any variant
        const preferredSource = `${targetCode}-${targetCode.toUpperCase()}`; // e.g., 'es-ES'
        if (Array.from(sourceLanguageEl.options).some(opt => opt.value === preferredSource)) {
            return preferredSource;
        }
        // Fallback to the first available source that matches the language code
        const firstMatch = Array.from(sourceLanguageEl.options).find(opt => opt.value.startsWith(targetCode + '-'));
        return firstMatch ? firstMatch.value : null;
    }

    function findBestTargetMatch(sourceCode) {
        // Example: source 'fr-FR' should map to target 'fr'
        const langPart = sourceCode.split('-')[0];
        if (Array.from(targetLanguageEl.options).some(opt => opt.value === langPart)) {
            return langPart;
        }
        // Handle special cases like 'yue' for Cantonese
        if (sourceCode.startsWith('yue')) return 'yue';
        if (sourceCode.startsWith('zh-HK')) return 'yue';
        return null;
    }

    async function startRecognition() {
        try {
            const authResponse = await fetch('/api/get_token');
            if (!authResponse.ok) throw new Error('Failed to get auth token');
            const { token, region } = await authResponse.json();

            const speechConfig = SpeechSDK.SpeechTranslationConfig.fromAuthorizationToken(token, region);
            speechConfig.speechRecognitionLanguage = sourceLanguageEl.value;
            speechConfig.addTargetLanguage(targetLanguageEl.value);

            const audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
            recognizer = new SpeechSDK.TranslationRecognizer(speechConfig, audioConfig);

            setupRecognizerEvents();
            recognizer.startContinuousRecognitionAsync(() => {
                isRecording = true;
                updateUIRecording(true);
            }, (err) => {
                updateUIError(`Error starting: ${err}`);
                stopRecognition();
            });
        } catch (error) {
            updateUIError(`Initialization failed: ${error.message}`);
        }
    }

    function stopRecognition() {
        if (recognizer) {
            recognizer.stopContinuousRecognitionAsync(() => {
                isRecording = false;
                recognizer.close();
                recognizer = null;
                updateUIRecording(false);
            });
        }
    }

    function setupRecognizerEvents() {
        recognizer.recognizing = (s, e) => {
            originalTextEl.value = e.result.text || "";
        };

        recognizer.recognized = (s, e) => {
            if (e.result.reason === SpeechSDK.ResultReason.TranslatedSpeech) {
                const original = e.result.text;
                const translation = e.result.translations.get(targetLanguageEl.value);
                
                originalTextEl.value = original;
                translatedTextEl.value = translation;
                playBtn.disabled = false;
                updateUIStatus("Translation complete! 🎉", "success");

                if (autoPlayToggle.checked) {
                    synthesizeAndPlay(translation, targetLanguageEl.value);
                }
            } else if (e.result.reason === SpeechSDK.ResultReason.NoMatch) {
                updateUIStatus("Could not recognize speech. Please try again.", "warning");
            }
        };

        recognizer.canceled = (s, e) => {
            updateUIError(`Canceled: ${e.reason}. Check mic permissions.`);
            stopRecognition();
        };

        recognizer.sessionStopped = (s, e) => {
            stopRecognition();
        };
    }

    async function synthesizeAndPlay(text, language) {
        if (!text) return;
        playBtn.disabled = true;
        playBtn.classList.add("playing");
        playBtn.innerHTML = "🔊 Playing...";
        
        try {
            const response = await fetch('/api/synthesize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, language }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `Synthesis failed: ${response.status}`);
            }

            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            audio.play();
            audio.onended = () => {
                playBtn.disabled = false;
                playBtn.classList.remove("playing");
                playBtn.innerHTML = "▶️ Play Translation";
            };
        } catch (error) {
            updateUIError(`Audio playback error: ${error.message}`);
            playBtn.disabled = false;
            playBtn.classList.remove("playing");
            playBtn.innerHTML = "▶️ Play Translation";
        }
    }

    // --- UI Update Functions ---
    function updateUIRecording(isRec) {
        if (isRec) {
            recordBtn.classList.add("recording");
            recordBtn.innerHTML = `<span class="mic-icon">⏹️</span> Stop Recording`;
            originalTextEl.value = "";
            translatedTextEl.value = "";
            playBtn.disabled = true;
            updateUIStatus("Listening... Speak now!", "info");
        } else {
            recordBtn.classList.remove("recording");
            recordBtn.innerHTML = `<span class="mic-icon">🎤</span> Start Recording`;
            if (!originalTextEl.value) {
                 updateUIStatus("Click 'Start Recording' and speak.", "light");
            }
        }
    }

    function updateUIStatus(message, type = "light") {
        statusEl.textContent = message;
        statusEl.className = `alert alert-${type} text-center`;
    }
    
    function updateUIError(message) {
        updateUIStatus(message, "danger");
    }
});