document.addEventListener('DOMContentLoaded', () => {
    const promptInput = document.getElementById('prompt-input');
    const submitBtn = document.getElementById('submit-btn');
    const loadingState = document.getElementById('loading-state');
    const resultsSection = document.getElementById('results-section');
    
    // Result elements
    const aiResponse = document.getElementById('ai-response');
    const mCategory = document.getElementById('metric-category');
    const mPriority = document.getElementById('metric-priority');
    const mSentiment = document.getElementById('metric-sentiment');
    const mConfidence = document.getElementById('metric-confidence');
    
    // Telemetry
    const tComplexity = document.getElementById('telemetry-complexity');
    const tTools = document.getElementById('telemetry-tools');
    const tGuardrails = document.getElementById('telemetry-guardrails');

    let bearerToken = null;

    // Auto-login to get a token behind the scenes
    async function authenticate() {
        try {
            // Attempt to login with the dummy account we used in tests
            let response = await fetch('/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: "testuser@example.com",
                    password: "testpassword123"
                })
            });

            // If login fails (user doesn't exist), sign them up automatically
            if (!response.ok) {
                response = await fetch('/auth/signup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        email: "testuser@example.com",
                        password: "testpassword123",
                        full_name: "Demo User"
                    })
                });
            }

            const data = await response.json();
            bearerToken = data.access_token;
            console.log("Authenticated successfully.");
        } catch (error) {
            console.error("Auth failed:", error);
            alert("Failed to authenticate with backend. Is it running?");
        }
    }

    // Initialize auth on load
    authenticate();

    submitBtn.addEventListener('click', async () => {
        const content = promptInput.value.trim();
        if (!content) return;

        if (!bearerToken) {
            await authenticate();
            if (!bearerToken) return; // If still no token, abort
        }

        // UI State: Loading
        submitBtn.disabled = true;
        promptInput.disabled = true;
        loadingState.classList.remove('hidden');
        resultsSection.classList.add('hidden');
        
        // Dynamic loading text to simulate agentic workflow
        const loadingTexts = [
            "Parsing intent...",
            "Querying vector database...",
            "Formulating plan...",
            "Executing tools...",
            "Evaluating response quality..."
        ];
        const textElement = document.getElementById('loading-text');
        let textIndex = 0;
        const interval = setInterval(() => {
            textIndex = (textIndex + 1) % loadingTexts.length;
            textElement.innerText = loadingTexts[textIndex];
        }, 2000);

        try {
            const response = await fetch('/tickets/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${bearerToken}`
                },
                body: JSON.stringify({ content })
            });

            clearInterval(interval);

            if (!response.ok) {
                throw new Error(`API returned ${response.status}`);
            }

            const data = await response.json();
            
            // Populate UI
            aiResponse.innerText = data.response || "No response generated. (Check if LLM is configured correctly)";
            
            mCategory.innerText = data.metadata.category || "Unknown";
            mPriority.innerText = data.metadata.priority || "Normal";
            mSentiment.innerText = data.metadata.sentiment || "Neutral";
            mConfidence.innerText = data.metadata.ai_confidence || "0";

            // Color code priority
            mPriority.className = "metric-value";
            if (data.metadata.priority) {
                mPriority.classList.add(`priority-${data.metadata.priority.toLowerCase()}`);
            }

            // Telemetry
            tComplexity.innerText = data.plan.complexity || "Low";
            
            if (data.tools_used && data.tools_used.length > 0) {
                tTools.innerText = data.tools_used.join(", ");
            } else {
                tTools.innerText = "None";
            }
            
            tGuardrails.innerText = data.evaluation.guardrails_passed ? "PASSED ✅" : "FAILED ❌";

            // Reveal Results
            loadingState.classList.add('hidden');
            resultsSection.classList.remove('hidden');
            
        } catch (error) {
            clearInterval(interval);
            console.error("Error processing request:", error);
            alert("An error occurred while processing your request. See console for details.");
            loadingState.classList.add('hidden');
        } finally {
            // Restore UI State
            submitBtn.disabled = false;
            promptInput.disabled = false;
        }
    });
});
