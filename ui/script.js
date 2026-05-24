document.addEventListener("DOMContentLoaded", () => {
    const orb = document.getElementById("jarvis-orb");
    const statusText = document.getElementById("status-text");
    const transcriptBox = document.getElementById("transcript-box");
    const micBtn = document.getElementById("mic-btn");
    const stopBtn = document.getElementById("stop-btn");
    const uploadBtn = document.getElementById("upload-btn");
    const fileUpload = document.getElementById("file-upload");
    const modeToggleBtn = document.getElementById("mode-toggle-btn");
    const textControls = document.getElementById("text-controls");
    const audioControls = document.getElementById("audio-controls");
    const centerCore = document.querySelector(".center-core");
    const datetimeDisplay = document.getElementById("datetime-display");
    
    const filePreviewContainer = document.getElementById("file-preview-container");
    const filePreviewImg = document.getElementById("file-preview-img");
    const filePreviewName = document.getElementById("file-preview-name");
    const filePreviewClose = document.getElementById("file-preview-close");

    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");

    let interimMsgDiv = null;

    // Speech & State Tracking
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    let isJarvisSpeaking = false;
    let isListening = false; // Is mic actively looking for a command (Push to Talk)

    let audioQueue = [];
    let isPlaying = false;
    let currentAudio = null;
    let finishedStreaming = false;
    let typeWriterInterval = null;
    let currentAbortController = null;
    
    window.accumulatedTranscript = '';
    window.submitTimer = null;
    window.micTimeout = null;
    window.selectedFile = null;

    function clearPreview() {
        window.selectedFile = null;
        if (fileUpload) fileUpload.value = "";
        if (filePreviewContainer) filePreviewContainer.style.display = "none";
        if (filePreviewImg) filePreviewImg.src = "";
    }

    function stopEverything() {
        if (currentAbortController) {
            currentAbortController.abort();
            currentAbortController = null;
        }
        if (currentAudio) {
            currentAudio.pause();
            currentAudio = null;
        }
        audioQueue = [];
        isPlaying = false;
        finishedStreaming = true;
        
        if (typeWriterInterval) {
            clearInterval(typeWriterInterval);
            typeWriterInterval = null;
        }
        
        if (window.submitTimer) {
            clearTimeout(window.submitTimer);
            window.submitTimer = null;
        }
        if (window.micTimeout) {
            clearTimeout(window.micTimeout);
            window.micTimeout = null;
        }
        
        window.accumulatedTranscript = '';
        
        stopListening();
        
        isJarvisSpeaking = false;
        chatInput.disabled = false;
        sendBtn.disabled = false;
        statusText.innerText = "SYSTEM IDLE. CLICK MIC TO ACTIVATE.";
        orb.classList.remove("listening");
    }

    if (stopBtn) {
        stopBtn.addEventListener("click", stopEverything);
    }

    let currentMode = "AUDIO"; // default mode

    if (modeToggleBtn) {
        modeToggleBtn.addEventListener("click", () => {
            if (currentMode === "AUDIO") {
                // Switch to TEXT MODE
                currentMode = "TEXT";
                modeToggleBtn.innerText = "TEXT MODE";
                modeToggleBtn.style.borderColor = "var(--core-blue)";
                modeToggleBtn.style.color = "var(--core-blue)";
                modeToggleBtn.style.background = "rgba(0, 210, 255, 0.1)";

                textControls.style.display = "flex";
                audioControls.style.display = "none";
                centerCore.style.display = "none";

                // Stop any listening if active
                if (isListening) stopListening();

            } else {
                // Switch to AUDIO MODE
                currentMode = "AUDIO";
                modeToggleBtn.innerText = "AUDIO MODE";
                modeToggleBtn.style.borderColor = "#00ffcc";
                modeToggleBtn.style.color = "#00ffcc";
                modeToggleBtn.style.background = "rgba(0, 255, 204, 0.1)";

                textControls.style.display = "none";
                audioControls.style.display = "flex";
                centerCore.style.display = "flex";
            }
        });
    }

    if (uploadBtn && fileUpload) {
        uploadBtn.addEventListener("click", () => {
            fileUpload.click();
        });

        fileUpload.addEventListener("change", (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = (ev) => {
                window.selectedFile = {
                    name: file.name,
                    data: ev.target.result,
                    mime: file.type
                };
                statusText.innerText = `[FILE ATTACHED]: ${file.name}`;
                
                if (filePreviewContainer) filePreviewContainer.style.display = "flex";
                if (filePreviewName) filePreviewName.innerText = file.name;
                
                if (file.type.startsWith("image/") && filePreviewImg) {
                    filePreviewImg.src = ev.target.result;
                    filePreviewImg.style.display = "block";
                } else if (filePreviewImg) {
                    filePreviewImg.src = "";
                    filePreviewImg.style.display = "none";
                }
            };
            reader.readAsDataURL(file);
        });
    }

    if (filePreviewClose) {
        filePreviewClose.addEventListener("click", () => {
            clearPreview();
            statusText.innerText = "SYSTEM IDLE. CLICK MIC TO ACTIVATE.";
        });
    }

    setInterval(() => {
        const now = new Date();
        datetimeDisplay.innerText = now.toTimeString().split(' ')[0] + " // " + now.toDateString().toUpperCase();
    }, 1000);

    function addMessage(role, text) {
        const msg = document.createElement("div");
        msg.className = `message ${role}`;
        msg.innerText = `[${role.toUpperCase()}] ${text}`;
        transcriptBox.appendChild(msg);
        transcriptBox.scrollTop = transcriptBox.scrollHeight;
        return msg;
    }

    async function typeWriter(element, text, speed = 30) {
        element.innerText = `[JARVIS] `;
        for (let i = 0; i < text.length; i++) {
            element.textContent += text.charAt(i);
            transcriptBox.scrollTop = transcriptBox.scrollHeight;
            await new Promise(r => setTimeout(r, speed));
        }
    }

    function stopListening() {
        if (isListening && recognition) {
            try { recognition.stop(); } catch(e) {}
        }
        isListening = false;
        orb.classList.remove("listening");
        statusText.innerText = "SYSTEM IDLE. CLICK MIC TO ACTIVATE.";
        if (interimMsgDiv) {
            interimMsgDiv.remove();
            interimMsgDiv = null;
        }
    }

    async function submitQuery(transcript) {
        if (!transcript.trim() && !window.selectedFile) return;
        
        if (window.submitTimer) {
            clearTimeout(window.submitTimer);
            window.submitTimer = null;
        }

        isJarvisSpeaking = true;
        stopListening(); // Turn off mic immediately upon processing

        let displayMsg = transcript;
        if (window.selectedFile) {
            displayMsg = `[Attached: ${window.selectedFile.name}] ` + displayMsg;
        }
        addMessage("Admin", displayMsg);
        
        statusText.innerText = "PROCESSING...";
        chatInput.value = "";
        chatInput.disabled = true;
        sendBtn.disabled = true;

        if (/goodbye|thank you|thanks|shut down|stop/i.test(transcript)) {
            const msgObj = addMessage("jarvis", "");
            await typeWriter(msgObj, "Shutting down. Goodbye, Sir.");
            statusText.innerText = "SYSTEM OFFLINE.";
            isJarvisSpeaking = false;
            chatInput.disabled = false;
            sendBtn.disabled = false;
            return;
        }

        currentAbortController = new AbortController();

        try {
            const payload = { text: transcript || "Please analyze this file." };
            if (window.selectedFile) {
                payload.file_data = window.selectedFile.data;
                payload.file_mime = window.selectedFile.mime;
            }

            const res = await fetch("http://127.0.0.1:8000/ask_stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
                signal: currentAbortController.signal
            });
            const msgObj = addMessage("jarvis", "");
            const reader = res.body.getReader();
            const decoder = new TextDecoder("utf-8");
            
            audioQueue = [];
            isPlaying = false;
            finishedStreaming = false;

            async function playNextAudio() {
                if (audioQueue.length === 0) {
                    if (finishedStreaming) {
                        isPlaying = false;
                    }
                    return;
                }
                isPlaying = true;
                const item = audioQueue.shift();
                currentAudio = new Audio("data:audio/mp3;base64," + item.audio);
                
                let displayedLength = 0;
                currentAudio.onloadedmetadata = () => {
                    const duration = currentAudio.duration * 1000;
                    // Slightly faster than audio to ensure text finishes right before audio ends
                    const charDelay = (duration * 0.85) / item.text.length; 
                    
                    typeWriterInterval = setInterval(() => {
                        if (displayedLength < item.text.length) {
                            msgObj.textContent += item.text.charAt(displayedLength);
                            transcriptBox.scrollTop = transcriptBox.scrollHeight;
                            displayedLength++;
                        } else {
                            clearInterval(typeWriterInterval);
                        }
                    }, charDelay);
                };
                
                currentAudio.onended = () => {
                    if(typeWriterInterval) clearInterval(typeWriterInterval);
                    if (displayedLength < item.text.length) {
                        msgObj.textContent += item.text.substring(displayedLength);
                        transcriptBox.scrollTop = transcriptBox.scrollHeight;
                    }
                    isPlaying = false;
                    playNextAudio();
                };
                currentAudio.play();
            }

            let buffer = "";
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                let lines = buffer.split("\n\n");
                buffer = lines.pop(); // keep the last partial chunk
                
                for (let line of lines) {
                    if (line.startsWith("data: ")) {
                        try {
                            const data = JSON.parse(line.substring(6));
                            if (data.type === "sentence_audio") {
                                audioQueue.push({ text: data.text, audio: data.audio });
                                if (!isPlaying) {
                                    playNextAudio();
                                }
                            }
                        } catch (e) {
                            console.error("Error parsing SSE data", e);
                        }
                    }
                }
            }
            
            finishedStreaming = true;
            if (!isPlaying && audioQueue.length > 0) {
                playNextAudio();
            }

            // Wait for audio to finish playing completely
            while (isPlaying || audioQueue.length > 0) {
                await new Promise(r => setTimeout(r, 500));
            }

        } catch (err) {
            if (err.name !== 'AbortError') {
                addMessage("system", "Uplink Error: " + err.message);
            }
        } finally {
            if (currentAbortController !== null) {
                isJarvisSpeaking = false;
                chatInput.disabled = false;
                sendBtn.disabled = false;
                chatInput.focus();
                
                // Clear the file preview since the interaction is finished
                clearPreview();
                
                // Revert back to completely idle mode once done
                statusText.innerText = "SYSTEM IDLE. CLICK MIC TO ACTIVATE.";
                orb.classList.remove("listening");
                
                // Enable mic for 3 seconds to allow user to say more ONLY in AUDIO mode
                if (currentMode === "AUDIO") {
                    triggerListening();
                    if (window.micTimeout) clearTimeout(window.micTimeout);
                    window.micTimeout = setTimeout(() => {
                        if (isListening) {
                            stopListening();
                        }
                    }, 3000);
                }
            }
        }
    }

    sendBtn.addEventListener("click", () => submitQuery(chatInput.value));
    chatInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            submitQuery(chatInput.value);
        }
    });

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false; // Stops naturally after one sentence
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
            isListening = true;
            orb.classList.add("listening");
            statusText.innerText = "LISTENING FOR COMMAND...";
            
            if (interimMsgDiv) interimMsgDiv.remove();
            interimMsgDiv = document.createElement("div");
            interimMsgDiv.className = `message user`;
            interimMsgDiv.style.opacity = "0.6";
            transcriptBox.appendChild(interimMsgDiv);
        };

        recognition.onresult = async (event) => {
            if (isJarvisSpeaking) return;

            if (window.micTimeout) {
                clearTimeout(window.micTimeout);
                window.micTimeout = null;
            }

            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }

            finalTranscript = finalTranscript.trim();

            if (interimTranscript) {
                statusText.innerText = `[HEARING]: ${interimTranscript}`;
                if (interimMsgDiv) {
                    interimMsgDiv.innerText = `[Admin] ${window.accumulatedTranscript} ${interimTranscript}...`;
                    transcriptBox.scrollTop = transcriptBox.scrollHeight;
                }
            }

            if (finalTranscript) {
                if (window.submitTimer) clearTimeout(window.submitTimer);
                
                window.accumulatedTranscript += finalTranscript + ' ';
                if (interimMsgDiv) {
                    interimMsgDiv.innerText = `[Admin] ${window.accumulatedTranscript}...`;
                    transcriptBox.scrollTop = transcriptBox.scrollHeight;
                }
                
                // Wait 1 second before submitting to allow for more speech
                window.submitTimer = setTimeout(() => {
                    let text = window.accumulatedTranscript.trim();
                    window.accumulatedTranscript = '';
                    if (text) submitQuery(text);
                }, 1000);
            }
        };

        recognition.onerror = (e) => {
            if (e.error === 'not-allowed') {
                addMessage("system", "Microphone access denied. Please allow it or use text input.");
            } else {
                console.log("Mic Error: ", e.error);
            }
            stopListening();
        };

        recognition.onend = () => {
            // Turn off UI properly if the mic naturally cuts out
            if (isListening && !window.submitTimer) {
                stopListening();
            }
        };

    } else {
        addMessage("system", "Speech Recognition not supported in this browser.");
    }

    const triggerListening = () => {
        if (!recognition) return;
        
        if (isListening) {
            // Click again to turn off
            stopListening();
        } else {
            // Click to start
            if (!isJarvisSpeaking) {
                try {
                    recognition.start();
                } catch(e) { }
            }
        }
    };

    orb.addEventListener("click", triggerListening);
    micBtn.addEventListener("click", triggerListening);
});
