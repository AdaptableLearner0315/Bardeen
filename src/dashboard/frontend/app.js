// Research Assistant Dashboard - Frontend JavaScript

// Configuration
const API_BASE_URL = window.location.origin;
const API_URL = `${API_BASE_URL}/api`;

// Global state
let currentTab = 'chat';
let evaluationList = [];
let currentEvaluation = null;
let currentMode = 'auto';  // 'auto', 'normal', or 'deep'

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    initializeChat();
    initializeEvaluations();
    initializeDataset();
    checkHealth();
});

// Tab Management
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');

    currentTab = tabName;

    // Load data for the tab
    if (tabName === 'evaluations' && evaluationList.length === 0) {
        loadEvaluations();
    } else if (tabName === 'dataset') {
        loadDataset();
    }
}

// Health Check
async function checkHealth() {
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();

        updateStatus(data.agent_initialized, data.available_tools);
    } catch (error) {
        updateStatus(false, []);
    }
}

function updateStatus(isOnline, tools) {
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    const toolsElement = document.getElementById('available-tools');

    if (isOnline) {
        statusDot.className = 'status-dot online';
        statusText.textContent = 'Connected';
        if (toolsElement) {
            toolsElement.textContent = tools.join(', ');
        }
    } else {
        statusDot.className = 'status-dot offline';
        statusText.textContent = 'Offline - Check API keys';
        if (toolsElement) {
            toolsElement.textContent = 'Not available';
        }
    }
}

// Chat Functionality
function initializeChat() {
    const sendButton = document.getElementById('send-button');
    const chatInput = document.getElementById('chat-input');

    sendButton.addEventListener('click', sendMessage);

    // Send on Enter key (Shift+Enter for new line)
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault(); // Prevent new line
            sendMessage();
        }
        // Shift+Enter allows new line (default behavior)
    });

    // Initialize mode toggle buttons
    initializeModeToggle();
}

function initializeModeToggle() {
    const autoBtn = document.getElementById('mode-auto');
    const normalBtn = document.getElementById('mode-normal');
    const deepBtn = document.getElementById('mode-deep');

    if (autoBtn) {
        autoBtn.addEventListener('click', () => {
            setMode('auto');
        });
    }

    if (normalBtn) {
        normalBtn.addEventListener('click', () => {
            setMode('normal');
        });
    }

    if (deepBtn) {
        deepBtn.addEventListener('click', () => {
            setMode('deep');
        });
    }
}

function setMode(mode) {
    currentMode = mode;

    // Update button states
    document.querySelectorAll('.mode-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`mode-${mode}`).classList.add('active');

    // Update indicator
    const modeIndicator = document.getElementById('mode-indicator');
    if (modeIndicator) {
        if (mode === 'auto') {
            modeIndicator.textContent = 'Mode: Auto (AI selects)';
            modeIndicator.style.color = '#4caf50';
        } else if (mode === 'normal') {
            modeIndicator.textContent = 'Mode: Normal (2-3 tools)';
            modeIndicator.style.color = '#666';
        } else {
            modeIndicator.textContent = 'Mode: Deep (5-10 tools)';
            modeIndicator.style.color = '#666';
        }
    }
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const resetCheckbox = document.getElementById('reset-conversation');
    const messagesContainer = document.getElementById('chat-messages');

    const message = input.value.trim();
    if (!message) return;

    // Disable input
    input.disabled = true;
    sendButton.disabled = true;

    // Add user message
    addMessage('user', message);

    // Add thinking indicator with animation
    const thinkingId = addThinkingIndicator();

    // Clear input
    input.value = '';

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                reset_conversation: resetCheckbox.checked,
                mode: currentMode
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Remove thinking indicator
        stopThinkingProgress();
        removeMessage(thinkingId);

        // Add assistant response
        addAssistantMessage(data);

        // Reset conversation checkbox
        resetCheckbox.checked = false;

    } catch (error) {
        stopThinkingProgress();
        removeMessage(thinkingId);
        addMessage('system', `Error: ${error.message}`);
    } finally {
        input.disabled = false;
        sendButton.disabled = false;
        input.focus();
    }
}

function addMessage(role, content) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageId = `msg-${Date.now()}`;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.id = messageId;

    if (role === 'user') {
        messageDiv.innerHTML = `
            <div class="message-header">You</div>
            <div class="message-content">${escapeHtml(content)}</div>
        `;
    } else if (role === 'system') {
        messageDiv.innerHTML = `<div class="message-content">${escapeHtml(content)}</div>`;
    }

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    return messageId;
}

function addAssistantMessage(data) {
    const messagesContainer = document.getElementById('chat-messages');

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';

    // Build execution plan ASCII art display
    let planHtml = '';
    if (data.execution_plan) {
        const plan = data.execution_plan;
        planHtml = `
            <div class="execution-plan">
                <div class="plan-header">
                    <span class="plan-icon">🎯</span>
                    <span class="plan-title">Execution Plan</span>
                </div>
                <pre class="plan-ascii">${escapeHtml(plan.ascii_plan || '')}</pre>
            </div>
        `;
    }

    // Build step-by-step tree visualization
    let treeHtml = '';
    if (data.execution_plan && data.execution_plan.steps && data.execution_plan.steps.length > 0) {
        const plan = data.execution_plan;
        const stepsHtml = plan.steps.map((step, index) => {
            const isLast = index === plan.steps.length - 1;
            const statusIcon = step.status === 'success' ? '✓' : (step.status === 'failed' ? '✗' : '○');
            const statusClass = step.status === 'success' ? 'success' : (step.status === 'failed' ? 'error' : 'pending');
            const statusLabel = step.status === 'success' ? 'PASS' : (step.status === 'failed' ? 'FAIL' : 'SKIP');

            return `
                <div class="tree-step ${statusClass}">
                    <div class="tree-connector">${isLast ? '└──' : '├──'}</div>
                    <div class="tree-content">
                        <div class="tree-step-header">
                            <span class="tree-step-num">Step ${step.step_number}</span>
                            <span class="tree-step-desc">${escapeHtml(step.description)}</span>
                            <span class="tree-status ${statusClass}">${statusIcon} ${statusLabel}</span>
                        </div>
                        <div class="tree-details">
                            <div class="tree-tool">
                                <span class="tree-label">Tool:</span>
                                <span class="tree-value">${escapeHtml(step.tool)}</span>
                            </div>
                            <div class="tree-reason">
                                <span class="tree-label">Why:</span>
                                <span class="tree-value">${escapeHtml(step.tool_reason)}</span>
                            </div>
                            ${step.latency_ms > 0 ? `<div class="tree-latency">${step.latency_ms.toFixed(0)}ms</div>` : ''}
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        treeHtml = `
            <div class="execution-tree">
                <div class="tree-header">
                    <span class="tree-icon">🌳</span>
                    <span class="tree-title">Step-by-Step Execution</span>
                </div>
                <div class="tree-goal">
                    <span class="goal-icon">🎯</span>
                    <span class="goal-text">${escapeHtml(plan.goal || 'Answer the question')}</span>
                </div>
                <div class="tree-steps">
                    ${stepsHtml}
                </div>
            </div>
        `;
    }

    // Build LLM thinking/reasoning trace (tool call details)
    let thinkingHtml = '';
    if (data.tool_calls && data.tool_calls.length > 0) {
        const thinkingSteps = data.tool_calls.map((t, index) => {
            const status = t.status === 'success' ? '✓' : '✗';
            const statusClass = t.status === 'success' ? 'success' : 'error';

            // Build reasoning display
            let reasoningHtml = '';
            if (t.llm_reasoning && t.llm_reasoning.trim()) {
                reasoningHtml = `<div class="reasoning">"${escapeHtml(t.llm_reasoning)}"</div>`;
            }

            // Build params display (show what was searched/calculated)
            let paramsHtml = '';
            if (t.params) {
                const paramEntries = Object.entries(t.params);
                if (paramEntries.length > 0) {
                    const paramStr = paramEntries.map(([k, v]) => {
                        const val = typeof v === 'string' ? v : JSON.stringify(v);
                        return `<span class="param-key">${k}:</span> <span class="param-value">"${escapeHtml(val.substring(0, 50))}${val.length > 50 ? '...' : ''}"</span>`;
                    }).join(', ');
                    paramsHtml = `<div class="tool-params">${paramStr}</div>`;
                }
            }

            return `
                <div class="thinking-step ${statusClass}">
                    <div class="step-header">
                        <span class="step-number">${index + 1}</span>
                        <span class="tool-name">${status} ${t.tool_name}</span>
                        <span class="step-latency">${t.latency_ms.toFixed(0)}ms</span>
                    </div>
                    ${reasoningHtml}
                    ${paramsHtml}
                </div>
            `;
        }).join('');

        thinkingHtml = `
            <details class="tool-details">
                <summary>
                    <strong>🔧 Tool Call Details</strong> (${data.tool_calls.length} call${data.tool_calls.length > 1 ? 's' : ''})
                </summary>
                <div class="thinking-trace">
                    ${thinkingSteps}
                </div>
            </details>
        `;
    }

    let toolsHtml = '';
    if (data.tool_calls && data.tool_calls.length > 0) {
        // Get unique tool names (deduplicated)
        const uniqueTools = [...new Set(data.tool_calls.map(t => t.tool_name))];
        toolsHtml = `
            <div class="tool-info">
                <strong>🔧 Tools used:</strong> ${uniqueTools.join(', ')}
            </div>
        `;
    }

    let asciiTraceHtml = '';
    if (data.ascii_trace) {
        asciiTraceHtml = `
            <details>
                <summary style="cursor: pointer; margin-top: 10px;">
                    <strong>📊 View Full Execution Trace</strong>
                </summary>
                <div class="ascii-trace">${escapeHtml(data.ascii_trace)}</div>
            </details>
        `;
    }

    // Show mode used with auto-detection indicator
    const modeUsed = data.mode || currentMode;
    const isAutoDetected = data.is_auto_detected || false;
    const modeIcon = modeUsed === 'deep' ? '🔬' : '🔍';
    const modeName = modeUsed === 'deep' ? 'Deep' : 'Normal';
    const modeLabel = isAutoDetected ? `✨ Auto → ${modeIcon} ${modeName}` : `${modeIcon} ${modeName}`;

    // Low confidence warning
    let lowConfidenceHtml = '';
    if (data.low_confidence) {
        lowConfidenceHtml = `
            <div class="low-confidence-warning">
                <span class="warning-icon">⚠️</span>
                <div class="warning-content">
                    <span class="warning-title">Low Confidence Answer</span>
                    <span class="warning-reason">${escapeHtml(data.low_confidence_reason || 'Tool limit reached')}</span>
                </div>
            </div>
        `;
    }

    messageDiv.innerHTML = `
        <div class="message-header">
            <span>Assistant <span style="font-size: 0.8rem; color: ${isAutoDetected ? '#4caf50' : '#888'};">(${modeLabel})</span></span>
            <span class="latency">${data.latency_ms.toFixed(0)}ms</span>
        </div>
        ${lowConfidenceHtml}
        ${planHtml}
        ${treeHtml}
        <div class="message-content">${formatAnswer(data.answer)}</div>
        ${toolsHtml}
        ${thinkingHtml}
        ${asciiTraceHtml}
    `;

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function removeMessage(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
        message.remove();
    }
}

function addThinkingIndicator() {
    const messagesContainer = document.getElementById('chat-messages');
    const messageId = `thinking-${Date.now()}`;

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message thinking-message';
    messageDiv.id = messageId;

    const modeText = currentMode === 'auto' ? 'Auto-detecting' : (currentMode === 'deep' ? 'Deep Research' : 'Normal');

    messageDiv.innerHTML = `
        <div class="thinking-container">
            <div class="thinking-animation">
                <div class="thinking-dot"></div>
                <div class="thinking-dot"></div>
                <div class="thinking-dot"></div>
            </div>
            <div class="thinking-text">
                <span class="thinking-title">Analyzing your request...</span>
                <span class="thinking-subtitle">${modeText} mode • Calling AI tools</span>
            </div>
            <div class="thinking-progress">
                <div class="progress-bar"></div>
            </div>
        </div>
    `;

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Start progress animation
    startThinkingProgress(messageId);

    return messageId;
}

let thinkingInterval = null;

function startThinkingProgress(messageId) {
    const steps = [
        'Analyzing your request...',
        'Selecting relevant tools...',
        'Gathering information...',
        'Processing with AI...',
        'Synthesizing results...'
    ];
    let stepIndex = 0;

    thinkingInterval = setInterval(() => {
        const messageDiv = document.getElementById(messageId);
        if (!messageDiv) {
            clearInterval(thinkingInterval);
            return;
        }

        const titleEl = messageDiv.querySelector('.thinking-title');
        if (titleEl) {
            stepIndex = (stepIndex + 1) % steps.length;
            titleEl.textContent = steps[stepIndex];
        }
    }, 2000);
}

function stopThinkingProgress() {
    if (thinkingInterval) {
        clearInterval(thinkingInterval);
        thinkingInterval = null;
    }
}

function formatAnswer(text) {
    // Convert newlines to <br>
    return escapeHtml(text).replace(/\n/g, '<br>');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Evaluations
function initializeEvaluations() {
    const refreshButton = document.getElementById('refresh-evaluations');
    const backButton = document.getElementById('back-to-list');

    refreshButton.addEventListener('click', loadEvaluations);
    backButton.addEventListener('click', showEvaluationList);
}

async function loadEvaluations() {
    const listContainer = document.getElementById('evaluation-list');
    listContainer.innerHTML = '<p class="loading">Loading evaluations...</p>';

    try {
        const response = await fetch(`${API_URL}/evaluations`);
        const data = await response.json();

        evaluationList = data.evaluations;

        if (evaluationList.length === 0) {
            listContainer.innerHTML = `
                <div style="text-align: center; padding: 40px;">
                    <p>No evaluation runs found.</p>
                    <p style="margin-top: 10px; color: #666;">
                        Run an evaluation with: <code>python run_evaluation.py</code>
                    </p>
                </div>
            `;
            return;
        }

        listContainer.innerHTML = '';

        evaluationList.forEach(eval => {
            const card = createEvaluationCard(eval);
            listContainer.appendChild(card);
        });

    } catch (error) {
        listContainer.innerHTML = `<p class="loading">Error loading evaluations: ${error.message}</p>`;
    }
}

function createEvaluationCard(eval) {
    const card = document.createElement('div');
    card.className = 'evaluation-card';
    card.onclick = () => loadEvaluationDetail(eval.run_id);

    const timestamp = new Date(eval.timestamp).toLocaleString();

    card.innerHTML = `
        <h3>${eval.run_id}</h3>
        <p style="color: #666; font-size: 0.9rem;">${timestamp}</p>
        <div class="eval-metrics">
            <div class="metric">
                <div class="metric-label">pass^5</div>
                <div class="metric-value ${eval.overall_pass_5 >= 0.8 ? 'success' : 'warning'}">
                    ${(eval.overall_pass_5 * 100).toFixed(0)}%
                </div>
            </div>
            <div class="metric">
                <div class="metric-label">pass^10</div>
                <div class="metric-value ${eval.overall_pass_10 >= 0.8 ? 'success' : 'warning'}">
                    ${(eval.overall_pass_10 * 100).toFixed(0)}%
                </div>
            </div>
            <div class="metric">
                <div class="metric-label">Consensus</div>
                <div class="metric-value">
                    ${(eval.avg_consensus_strength * 100).toFixed(0)}%
                </div>
            </div>
            <div class="metric">
                <div class="metric-label">Questions</div>
                <div class="metric-value">
                    ${eval.dataset_size}
                </div>
            </div>
        </div>
    `;

    return card;
}

async function loadEvaluationDetail(runId) {
    const listContainer = document.getElementById('evaluation-list');
    const detailContainer = document.getElementById('evaluation-detail');
    const detailContent = document.getElementById('evaluation-detail-content');

    listContainer.style.display = 'none';
    detailContainer.style.display = 'block';
    detailContent.innerHTML = '<p class="loading">Loading evaluation details...</p>';

    try {
        const response = await fetch(`${API_URL}/evaluations/${runId}`);
        const data = await response.json();

        currentEvaluation = data;

        detailContent.innerHTML = renderEvaluationDetail(data);

    } catch (error) {
        detailContent.innerHTML = `<p class="loading">Error loading details: ${error.message}</p>`;
    }
}

function renderEvaluationDetail(eval) {
    const timestamp = new Date(eval.timestamp).toLocaleString();

    let html = `
        <h2>${eval.run_id}</h2>
        <p style="color: #666; margin-bottom: 20px;">${timestamp}</p>

        <div class="eval-metrics">
            <div class="metric">
                <div class="metric-label">pass^5</div>
                <div class="metric-value success">${(eval.overall_pass_5 * 100).toFixed(1)}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">pass^10</div>
                <div class="metric-value success">${(eval.overall_pass_10 * 100).toFixed(1)}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Consensus</div>
                <div class="metric-value">${(eval.avg_consensus_strength * 100).toFixed(1)}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Avg Latency</div>
                <div class="metric-value">${eval.avg_latency_ms.toFixed(0)}ms</div>
            </div>
            <div class="metric">
                <div class="metric-label">Error Recovery</div>
                <div class="metric-value">${(eval.error_recovery_rate * 100).toFixed(1)}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Questions</div>
                <div class="metric-value">${eval.dataset_size}</div>
            </div>
        </div>

        <h3 style="margin-top: 30px; margin-bottom: 15px;">By Category</h3>
        <div class="eval-metrics">
    `;

    for (const [category, metrics] of Object.entries(eval.category_metrics)) {
        html += `
            <div class="metric">
                <div class="metric-label">${category}</div>
                <div style="font-size: 0.9rem; margin-top: 5px;">
                    pass^5: ${(metrics.pass_5_rate * 100).toFixed(0)}%<br>
                    pass^10: ${(metrics.pass_10_rate * 100).toFixed(0)}%
                </div>
            </div>
        `;
    }

    html += `
        </div>

        <h3 style="margin-top: 30px; margin-bottom: 15px;">Question Results</h3>
    `;

    eval.question_results.forEach(q => {
        const pass5Icon = q.pass_5 ? '✓' : '✗';
        const pass10Icon = q.pass_10 ? '✓' : '✗';

        html += `
            <div class="question-card">
                <div class="question-header">
                    <span class="question-id">${q.question_id}</span>
                    <span class="question-category">${q.category}</span>
                </div>
                <div class="question-text">${escapeHtml(q.question_text)}</div>
                <div style="display: flex; gap: 20px; margin-top: 10px; font-size: 0.9rem;">
                    <span>pass^5: ${pass5Icon}</span>
                    <span>pass^10: ${pass10Icon}</span>
                    <span>Consensus: ${(q.consensus_strength * 100).toFixed(0)}%</span>
                    <span>Latency: ${q.avg_latency_ms.toFixed(0)}ms</span>
                </div>
            </div>
        `;
    });

    return html;
}

function showEvaluationList() {
    document.getElementById('evaluation-list').style.display = 'block';
    document.getElementById('evaluation-detail').style.display = 'none';
    currentEvaluation = null;
}

// Dataset
function initializeDataset() {
    // Dataset loads when tab is switched
}

async function loadDataset() {
    const statsContainer = document.getElementById('dataset-stats');
    const questionsContainer = document.getElementById('dataset-questions');

    statsContainer.innerHTML = '<p class="loading">Loading dataset...</p>';
    questionsContainer.innerHTML = '';

    try {
        const response = await fetch(`${API_URL}/dataset`);
        const data = await response.json();

        // Render statistics
        let statsHtml = `
            <h3>Dataset Statistics</h3>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value">${data.statistics.total_questions}</div>
                    <div class="stat-label">Total Questions</div>
                </div>
        `;

        for (const [category, count] of Object.entries(data.statistics.categories)) {
            statsHtml += `
                <div class="stat-item">
                    <div class="stat-value">${count}</div>
                    <div class="stat-label">${category}</div>
                </div>
            `;
        }

        statsHtml += '</div>';
        statsContainer.innerHTML = statsHtml;

        // Render questions
        data.questions.forEach(q => {
            const card = document.createElement('div');
            card.className = 'question-card';

            card.innerHTML = `
                <div class="question-header">
                    <span class="question-id">${q.id}</span>
                    <span class="question-category">${q.category}</span>
                </div>
                <div class="question-text">${escapeHtml(q.question)}</div>
                <div class="question-tools">
                    <strong>Expected tools:</strong> ${q.expected_tools.join(', ')}
                </div>
            `;

            questionsContainer.appendChild(card);
        });

    } catch (error) {
        statsContainer.innerHTML = `<p class="loading">Error loading dataset: ${error.message}</p>`;
    }
}
