document.addEventListener("DOMContentLoaded", () => {
    const orb = document.getElementById("jarvis-orb");
    const statusText = document.getElementById("status-text");
    const transcriptBox = document.getElementById("transcript-box");
    const micBtn = document.getElementById("mic-btn");
    const datetimeDisplay = document.getElementById("datetime-display");

    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");

    let interimMsgDiv = null;

    // Speech & State Tracking
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    let isJarvisSpeaking = false;
    let isListening = false; // Is mic actively looking for a command (Push to Talk)

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
        if (!transcript.trim()) return;
        
        isJarvisSpeaking = true;
        stopListening(); // Turn off mic immediately upon processing

        addMessage("Admin", transcript);
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

        try {
            const res = await fetch("http://127.0.0.1:8000/ask_stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: transcript })
            });
            const msgObj = addMessage("jarvis", "");
            const reader = res.body.getReader();
            const decoder = new TextDecoder("utf-8");
            
            let audioQueue = [];
            let isPlaying = false;
            let currentAudio = null;
            let finishedStreaming = false;
            let typeWriterInterval = null;

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
                            msgObj.textContent += " ";
                            clearInterval(typeWriterInterval);
                        }
                    }, charDelay);
                };
                
                currentAudio.onended = () => {
                    if(typeWriterInterval) clearInterval(typeWriterInterval);
                    if (displayedLength < item.text.length) {
                        msgObj.textContent += item.text.substring(displayedLength) + " ";
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
            addMessage("system", "Uplink Error: " + err.message);
        } finally {
            isJarvisSpeaking = false;
            chatInput.disabled = false;
            sendBtn.disabled = false;
            chatInput.focus();
            
            // Revert back to completely idle mode once done
            statusText.innerText = "SYSTEM IDLE. CLICK MIC TO ACTIVATE.";
            orb.classList.remove("listening");
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
                    interimMsgDiv.innerText = `[Admin] ${interimTranscript}...`;
                    transcriptBox.scrollTop = transcriptBox.scrollHeight;
                }
            }

            if (finalTranscript) {
                // Instantly submit and turn off mic
                await submitQuery(finalTranscript);
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
            if (isListening) {
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
