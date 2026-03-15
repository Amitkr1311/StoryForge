const SAMPLE = `A small logistics startup was drowning in manual data-entry errors, losing thousands of dollars weekly and burning out their entire team. They had tried spreadsheets, sticky notes, and three different project management tools — nothing stuck. Then they implemented our AI-powered operations platform, and within two weeks, error rates dropped by 94 percent. Today their team focuses on strategic growth instead of firefighting, and they have successfully scaled to three new cities in just six months.`;

function sanitizeError(msg) {
    if (!msg) return "An unknown error occurred.";
    
    // 1. Detect status code patterns
    let status = "";
    const httpMatch = msg.match(/HTTP\s?(\d{3})/i);
    if (httpMatch) status = `[CODE ${httpMatch[1]}] `;

    // 2. Handle technical SDK/Python response strings
    if (msg.includes('Stability AI failed')) {
        try {
            const parts = msg.split(' — ');
            if (parts.length > 1) {
                const jsonPart = JSON.parse(parts[1]);
                if (jsonPart.errors && jsonPart.errors[0]) return `${status}STABILITY AI: ${jsonPart.errors[0]}`;
            }
        } catch(e) {}
    }

    if (msg.includes('Gemini returned no image') || msg.includes('HttpResponse') || msg.includes('sdk_http_response')) {
        return `${status}IMAGE ENGINE FAILURE: The provider returned an empty or invalid response.`;
    }
    
    // 3. General fallback: strip JSON noise and take first line
    let clean = msg.split('\n')[0].replace(/\{"errors":\["/g, "").split('","id"')[0].replace(/"\]/g, "");
    
    // If it still looks too technical (contains code-like markers), go generic
    if (clean.includes('=') || clean.includes('(') || clean.includes('{')) {
        return `${status}SYSTEM ERROR: Generation process was interrupted.`;
    }

    return status + clean;
}

const textArea = document.getElementById('pitch-text');
const charCount = document.getElementById('char-count');

function updateCount() {
    if (!textArea || !charCount) return;
    const len = textArea.value.length;
    charCount.textContent = len;
    charCount.style.color = len > 2800 ? '#e7390d' : '';
}

function loadSample() {
    if (textArea) {
        textArea.value = SAMPLE;
        updateCount();
    }
}

if (textArea) {
    textArea.addEventListener('input', updateCount);
}

/**
 * Safely appends an error row to the terminal without using innerHTML on untrusted strings.
 */
function termAppendError(term, message) {
    const row = document.createElement('div');
    row.className = 'flex items-center gap-2 mt-1 text-primary';

    const label = document.createElement('span');
    label.className = 'font-bold';
    label.textContent = 'ERROR:';

    const text = document.createElement('span');
    text.textContent = message;

    row.appendChild(label);
    row.appendChild(text);
    term.appendChild(row);
    term.scrollTop = term.scrollHeight;
}

/**
 * Safely appends a status line to the terminal.
 * Returns the created row element so callers can mutate it.
 */
function termAppendLine(term, message, extraClass = '') {
    const row = document.createElement('div');
    row.className = `flex items-center gap-2 mt-1 term-line ${extraClass}`.trim();

    const dot = document.createElement('span');
    dot.className = 'animate-pulse';
    dot.textContent = '●';

    const text = document.createElement('span');
    text.className = 'flex-1';
    text.textContent = message;

    row.appendChild(dot);
    row.appendChild(text);
    term.appendChild(row);
    term.scrollTop = term.scrollHeight;
    return row;
}

const pitchForm = document.getElementById('pitch-form');
if (pitchForm) {
    pitchForm.addEventListener('submit', async function(e) {
        e.preventDefault(); // Prevent standard POST
        const text = textArea.value.trim();
        if (!text) { return; }

        const term = document.getElementById('loading-terminal');
        const termIdle = document.getElementById('term-idle');
        const termIdleText = document.getElementById('term-idle-text');
        
        const submitBtnEl = document.getElementById('submit-btn');
        submitBtnEl.disabled = true;
        submitBtnEl.innerHTML = `GENERATING STORYBOARD...`;

        // Matrix Hacker Text Effect for initial terminal loading
        const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*";
        let glitchInterval;
        if (termIdleText) {
            let iteration = 0;
            const targetText = "INITIALIZING_PIPELINE";
            glitchInterval = setInterval(() => {
                termIdleText.innerText = targetText.split("")
                    .map((letter, index) => {
                        if(index < iteration) {
                            return targetText[index];
                        }
                        return chars[Math.floor(Math.random() * 42)]
                    })
                    .join("");
                if(iteration >= targetText.length){ 
                    clearInterval(glitchInterval);
                }
                iteration += 1 / 3;
            }, 30);
        }

        // Animated Latent Space Dashboard
        const grid = document.getElementById('plates-grid');
        const icon = grid.querySelector('.plate-icon');
        const scanBar = grid.querySelector('.scan-bar');
        const coordVal = document.getElementById('val-1');

        // Capture and remove whatever idle opacity class is currently set
        const idleOpacityClass = [...grid.classList].find(c => c.startsWith('opacity-') && c !== 'opacity-100') || 'opacity-50';
        grid.classList.remove(idleOpacityClass);
        grid.classList.add('opacity-100');
        
        if (icon) icon.classList.add('animate-spin');
        if (scanBar) {
            scanBar.classList.remove('opacity-0');
            scanBar.classList.add('animate-scan');
        }

        // Randomize coordinate value
        let coordInterval = setInterval(() => {
            if (coordVal) coordVal.textContent = (Math.random()).toFixed(2);
        }, 150);

        const stopAnimations = () => {
            grid.classList.remove('opacity-100');
            grid.classList.add(idleOpacityClass);
            if (icon) icon.classList.remove('animate-spin');
            if (scanBar) {
                scanBar.classList.remove('animate-scan');
                scanBar.classList.add('opacity-0');
            }
            clearInterval(coordInterval);
        };

        try {
            const formData = new FormData(this);
            const response = await fetch('/generate', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            
            if (!response.ok) {
                termAppendError(term, sanitizeError(data.error));
                submitBtnEl.disabled = false;
                submitBtnEl.textContent = 'GENERATE STORYBOARD';
                stopAnimations();
                return;
            }
            
            setTimeout(() => {
                if (glitchInterval) clearInterval(glitchInterval);
                if (termIdle) termIdle.style.display = 'none';
                term.innerHTML = ''; // Start pristine terminal log
            }, 1000); // Leave the cool glitch text for 1 sec minimum

            const eventSource = new EventSource(`/stream/${data.task_id}`);
            
            eventSource.onmessage = function(event) {
                const payload = JSON.parse(event.data);
                
                if (payload.status === 'error') {
                    eventSource.close();
                    termAppendError(term, sanitizeError(payload.error));
                    submitBtnEl.disabled = false;
                    submitBtnEl.textContent = 'GENERATE STORYBOARD';
                    stopAnimations();
                    return;
                }
                
                if (payload.status === 'complete') {
                    eventSource.close();
                    document.open();
                    document.write(payload.html);
                    document.close();
                    return;
                }
                
                const lines = term.querySelectorAll('.term-line');
                const lastLineEl = lines.length > 0 ? lines[lines.length - 1] : null;
                const lastText = lastLineEl ? lastLineEl.querySelector('span:last-child').innerText : "";
                
                // Determine if this is an "update" to the current line (e.g. [IN PROGRESS] -> [OK])
                const isUpdate = lastText.includes('...') && 
                                 payload.message.includes('...') && 
                                 lastText.split('...')[0] === payload.message.split('...')[0];

                if (isUpdate) {
                    // Update the existing line's text
                    const textSpan = lastLineEl.querySelector('span:last-child');
                    textSpan.innerText = payload.message;
                    
                    // If it's no longer in progress, stop the pulse
                    if (payload.message.includes('[OK]')) {
                        const pulse = lastLineEl.querySelector('.animate-pulse');
                        if (pulse) {
                            pulse.classList.remove('animate-pulse');
                            pulse.innerText = '○';
                        }
                    }
                } else if (lastText !== payload.message) {
                    // Stop previous animations
                    const oldPulses = term.querySelectorAll('.animate-pulse');
                    oldPulses.forEach(el => {
                        el.classList.remove('animate-pulse');
                        if (el.textContent === '●') el.textContent = '○';
                    });

                    const highlightClass = payload.status === 'generating' ? 'text-primary' : '';
                    termAppendLine(term, payload.message, highlightClass);
                }
                term.scrollTop = term.scrollHeight;
            };
            
            eventSource.onerror = function() {
                eventSource.close();
                termAppendError(term, 'CONNECTION LOST TO BACKGROUND PIPELINE');
                submitBtnEl.disabled = false;
                submitBtnEl.textContent = 'GENERATE STORYBOARD';
                stopAnimations();
            };

        } catch (err) {
            termAppendError(term, sanitizeError(err.message));
            submitBtnEl.disabled = false;
            submitBtnEl.textContent = 'GENERATE STORYBOARD';
            stopAnimations();
        }
    });
}

// Rotating Quotes Logic
const quoteEl = document.getElementById('quote-text');
if (quoteEl) {
    const quotes = [
        `"A <span class="font-bebas not-italic text-5xl lg:text-6xl text-primary block my-2 tracking-tight">GREAT STORY</span> told badly is still a great story. A great story told visually is <span class="underline decoration-1 underline-offset-8">unforgettable</span>."`,
        `"Show, <span class="font-bebas not-italic text-5xl lg:text-6xl text-primary block my-2 tracking-tight">DON'T TELL</span>. Let the imagery speak volumes where <span class="underline decoration-1 underline-offset-8">words fall short</span>."`,
        `"Every great film, product, or movement started as a <span class="font-bebas not-italic text-5xl lg:text-6xl text-primary block my-2 tracking-tight">CLEAR VISION</span>."`,
        `"Before they build it, they must <span class="underline decoration-1 underline-offset-8">believe it</span>. <span class="font-bebas not-italic text-5xl lg:text-6xl text-primary block my-2 tracking-tight">VISUALS</span> bridge that gap."`,
        `"Translate your narrative into a <span class="font-bebas not-italic text-5xl lg:text-6xl text-primary block my-2 tracking-tight">CINEMATIC EXPERIENCE</span>, one frame at a time."`,
        `"The difference between a good pitch and a <span class="underline decoration-1 underline-offset-8">funded pitch</span> is <span class="font-bebas not-italic text-5xl lg:text-6xl text-primary block my-2 tracking-tight">WHAT THEY CAN SEE</span>."`
    ];
    let quoteIndex = 0;
    setInterval(() => {
        quoteEl.classList.remove('opacity-100');
        quoteEl.classList.add('opacity-0');
        setTimeout(() => {
            quoteIndex = (quoteIndex + 1) % quotes.length;
            quoteEl.innerHTML = quotes[quoteIndex];
            quoteEl.classList.remove('opacity-0');
            quoteEl.classList.add('opacity-100');
        }, 1000);
    }, 6000);
}

// Dynamic Timecode Logic
const tcEl = document.getElementById('tc-counter');
if (tcEl) {
    let frames = 2, seconds = 44, minutes = 12, hours = 0;
    const pad = (n) => n.toString().padStart(2, '0');
    setInterval(() => {
        frames += 1;
        if (frames >= 24) { frames = 0; seconds += 1; }
        if (seconds >= 60) { seconds = 0; minutes += 1; }
        tcEl.innerText = `TC: ${pad(hours)}:${pad(minutes)}:${pad(seconds)}:${pad(frames)}`;
        
        const fpsEl = document.getElementById('fps-counter');
        if(fpsEl && Math.random() > 0.8) {
            fpsEl.innerText = (23.970 + Math.random() * 0.010).toFixed(3);
        }
    }, 1000 / 24);
}
