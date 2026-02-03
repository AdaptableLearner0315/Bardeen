// Research Assistant Dashboard - Frontend JavaScript

// Configuration
const API_BASE_URL = window.location.origin;
const API_URL = `${API_BASE_URL}/api`;

// Global state
let currentTab = 'chat';
let evaluationList = [];
let currentEvaluation = null;
let currentMode = 'auto';  // 'auto', 'normal', or 'deep'

// Helper function to safely format numbers
function safeFixed(value, decimals = 1, defaultValue = 0) {
    if (value === undefined || value === null || isNaN(value)) {
        return defaultValue.toFixed(decimals);
    }
    return Number(value).toFixed(decimals);
}

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

    if (isOnline) {
        statusDot.className = 'status-dot online';
        statusText.textContent = 'Connected';
    } else {
        statusDot.className = 'status-dot offline';
        statusText.textContent = 'Offline - Check API keys';
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

    // Update button states (works with both .mode-button and .mode-icon)
    document.querySelectorAll('.mode-icon, .mode-button').forEach(btn => {
        btn.classList.remove('active');
    });
    const modeBtn = document.getElementById(`mode-${mode}`);
    if (modeBtn) modeBtn.classList.add('active');

    // Update compact indicator
    const modeIndicator = document.getElementById('mode-indicator');
    if (modeIndicator) {
        if (mode === 'auto') {
            modeIndicator.textContent = '✨ Auto';
            modeIndicator.style.background = '#f0fdf4';
            modeIndicator.style.color = '#166534';
        } else if (mode === 'normal') {
            modeIndicator.textContent = '⚡ Normal';
            modeIndicator.style.background = '#eff6ff';
            modeIndicator.style.color = '#1e40af';
        } else {
            modeIndicator.textContent = '🔬 Deep';
            modeIndicator.style.background = '#f5f3ff';
            modeIndicator.style.color = '#5b21b6';
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

    // Build Multi-Agent Routing section
    let routingHtml = '';
    if (data.multi_agent_routing) {
        const routing = data.multi_agent_routing;
        const agentsHtml = routing.agents.map(a => `
            <div class="agent-badge">
                <span class="agent-icon">${a.icon}</span>
                <span class="agent-name">${a.display_name}</span>
            </div>
        `).join('');

        routingHtml = `
            <div class="routing-info">
                <div class="routing-header">
                    <strong>🧠 Agent Routing:</strong>
                    <span class="routing-mode ${routing.mode}">${routing.mode === 'multi_agent' ? 'Multi-Agent' : 'Single Agent'}</span>
                </div>
                <div class="agents-used">${agentsHtml}</div>
                <div class="routing-reasoning">${escapeHtml(routing.routing_reasoning)}</div>
            </div>
        `;
    }

    // Build Agent Execution Details section
    let agentExecutionsHtml = '';
    if (data.agent_executions && data.agent_executions.length > 0) {
        const executionsContent = data.agent_executions.map(agent => {
            const toolsList = agent.tools_used.map((t, idx) => {
                const status = t.status === 'success' ? '✓' : '✗';
                const statusClass = t.status === 'success' ? 'success' : 'error';

                let paramsStr = '';
                if (t.params) {
                    const entries = Object.entries(t.params);
                    if (entries.length > 0) {
                        paramsStr = entries.map(([k, v]) => {
                            const val = typeof v === 'string' ? v : JSON.stringify(v);
                            return `${k}: "${val.substring(0, 40)}${val.length > 40 ? '...' : ''}"`;
                        }).join(', ');
                    }
                }

                let reasoningStr = '';
                if (t.reasoning && t.reasoning.trim()) {
                    reasoningStr = `<div class="tool-reasoning">"${escapeHtml(t.reasoning)}"</div>`;
                }

                return `
                    <div class="agent-tool-call ${statusClass}">
                        <div class="tool-header">
                            <span class="tool-status">${status}</span>
                            <span class="tool-name">${t.tool}</span>
                            <span class="tool-latency">${t.latency_ms.toFixed(0)}ms</span>
                        </div>
                        ${paramsStr ? `<div class="tool-params-mini">${escapeHtml(paramsStr)}</div>` : ''}
                        ${reasoningStr}
                    </div>
                `;
            }).join('');

            const successPercent = (agent.success_rate * 100).toFixed(0);

            return `
                <div class="agent-execution">
                    <div class="agent-exec-header">
                        <span class="agent-icon">${agent.icon}</span>
                        <span class="agent-name">${agent.display_name}</span>
                        <span class="agent-stats">${agent.tool_count} tool${agent.tool_count > 1 ? 's' : ''} • ${agent.total_latency_ms.toFixed(0)}ms • ${successPercent}% success</span>
                    </div>
                    <div class="agent-tools-list">
                        ${toolsList}
                    </div>
                </div>
            `;
        }).join('');

        agentExecutionsHtml = `
            <details class="agent-executions-details" open>
                <summary>
                    <strong>🤖 Agent Execution Details</strong> (${data.agent_executions.length} agent${data.agent_executions.length > 1 ? 's' : ''})
                </summary>
                <div class="agent-executions-content">
                    ${executionsContent}
                </div>
            </details>
        `;
    }

    // Build simple tools summary
    let toolsHtml = '';
    if (data.tool_calls && data.tool_calls.length > 0) {
        const uniqueTools = [...new Set(data.tool_calls.map(t => t.tool_name))];
        toolsHtml = `
            <div class="tool-info">
                <strong>🔧 Tools used:</strong> ${uniqueTools.join(', ')}
            </div>
        `;
    }

    // Build legacy tool call details (collapsed)
    let thinkingHtml = '';
    if (data.tool_calls && data.tool_calls.length > 0) {
        const thinkingSteps = data.tool_calls.map((t, index) => {
            const status = t.status === 'success' ? '✓' : '✗';
            const statusClass = t.status === 'success' ? 'success' : 'error';

            let reasoningHtml = '';
            if (t.llm_reasoning && t.llm_reasoning.trim()) {
                reasoningHtml = `<div class="reasoning">"${escapeHtml(t.llm_reasoning)}"</div>`;
            }

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
                    <strong>📋 Raw Tool Call Trace</strong> (${data.tool_calls.length} call${data.tool_calls.length > 1 ? 's' : ''})
                </summary>
                <div class="thinking-trace">
                    ${thinkingSteps}
                </div>
            </details>
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
            <span>Assistant <span class="mode-badge ${isAutoDetected ? 'auto' : ''}">${modeLabel}</span></span>
            <span class="latency">${data.latency_ms.toFixed(0)}ms</span>
        </div>
        ${lowConfidenceHtml}
        <div class="message-content">${formatAnswer(data.answer)}</div>
        ${routingHtml}
        ${toolsHtml}
        ${agentExecutionsHtml}
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

    messageDiv.innerHTML = `
        <div class="thinking-container">
            <div class="thinking-animation">
                <div class="thinking-dot"></div>
                <div class="thinking-dot"></div>
                <div class="thinking-dot"></div>
            </div>
            <div class="thinking-text">
                <span class="thinking-title">🧠 Routing to specialist agents...</span>
                <span class="thinking-subtitle"></span>
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
        { title: '🧠 Routing to specialist agents...', subtitle: 'Analyzing query intent' },
        { title: '🏢 Company Research Agent', subtitle: 'Searching company data...' },
        { title: '📊 Financial Analyst Agent', subtitle: 'Analyzing market data...' },
        { title: '🔍 Competitive Intel Agent', subtitle: 'Comparing alternatives...' },
        { title: '🔧 Executing tool calls...', subtitle: 'web_search, wikipedia, calculator' },
        { title: '✨ Synthesizing responses...', subtitle: 'Merging agent outputs' }
    ];
    let stepIndex = 0;

    thinkingInterval = setInterval(() => {
        const messageDiv = document.getElementById(messageId);
        if (!messageDiv) {
            clearInterval(thinkingInterval);
            return;
        }

        const titleEl = messageDiv.querySelector('.thinking-title');
        const subtitleEl = messageDiv.querySelector('.thinking-subtitle');
        if (titleEl && subtitleEl) {
            stepIndex = (stepIndex + 1) % steps.length;
            titleEl.textContent = steps[stepIndex].title;
            subtitleEl.textContent = steps[stepIndex].subtitle;
        }
    }, 1500);
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
        // Use b2b-evaluations endpoint for B2B evaluation results
        const response = await fetch(`${API_URL}/b2b-evaluations`);
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
        console.error('Error loading evaluations:', error);
        listContainer.innerHTML = `<p class="loading">Error loading evaluations: ${error.message}</p>`;
    }
}

function createEvaluationCard(eval) {
    const card = document.createElement('div');
    card.className = 'evaluation-card';
    card.onclick = () => loadEvaluationDetail(eval.run_id);

    const timestamp = new Date(eval.timestamp).toLocaleString();

    // Handle both B2B evaluation format and legacy format
    const passRate = eval.overall_pass_rate !== undefined ? eval.overall_pass_rate : eval.overall_pass_5;
    const avgScore = eval.avg_accuracy_score !== undefined ? eval.avg_accuracy_score : 0;
    const toolPrecision = eval.tool_precision !== undefined ? eval.tool_precision : 0;
    const questionCount = eval.total_questions !== undefined ? eval.total_questions : eval.dataset_size;

    card.innerHTML = `
        <h3>${eval.run_id}</h3>
        <p style="color: #666; font-size: 0.9rem;">${timestamp}</p>
        <div class="eval-metrics">
            <div class="metric">
                <div class="metric-label">Pass Rate</div>
                <div class="metric-value ${passRate >= 0.75 ? 'success' : 'warning'}">
                    ${(passRate * 100).toFixed(0)}%
                </div>
            </div>
            <div class="metric">
                <div class="metric-label">Avg Score</div>
                <div class="metric-value ${avgScore >= 70 ? 'success' : 'warning'}">
                    ${avgScore.toFixed(1)}
                </div>
            </div>
            <div class="metric">
                <div class="metric-label">Tool Precision</div>
                <div class="metric-value">
                    ${(toolPrecision * 100).toFixed(0)}%
                </div>
            </div>
            <div class="metric">
                <div class="metric-label">Questions</div>
                <div class="metric-value">
                    ${questionCount}
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
        // Use B2B evaluation endpoint for B2B results
        const response = await fetch(`${API_URL}/b2b-evaluations/${runId}`);
        const data = await response.json();

        currentEvaluation = data;

        detailContent.innerHTML = renderEvaluationDetail(data);

    } catch (error) {
        console.error('Error loading evaluation detail:', error);
        detailContent.innerHTML = `<p class="loading">Error loading details: ${error.message}</p>`;
    }
}

function renderEvaluationDetail(eval) {
    const timestamp = new Date(eval.timestamp).toLocaleString();

    // Check if this is a B2B evaluation (has overall_pass_rate) or legacy format
    const isB2BEval = eval.overall_pass_rate !== undefined;

    let html = `
        <h2>${eval.run_id}</h2>
        <p style="color: #666; margin-bottom: 20px;">${timestamp}</p>

        <div class="eval-metrics">
    `;

    if (isB2BEval) {
        // B2B evaluation format - use safeFixed for all numeric values
        html += `
            <div class="metric">
                <div class="metric-label">Pass Rate</div>
                <div class="metric-value success">${safeFixed((eval.overall_pass_rate || 0) * 100, 1)}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Avg Score</div>
                <div class="metric-value">${safeFixed(eval.avg_accuracy_score, 1)}/100</div>
            </div>
            <div class="metric">
                <div class="metric-label">Tool Precision</div>
                <div class="metric-value">${safeFixed((eval.tool_precision || 0) * 100, 1)}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Avg Depth</div>
                <div class="metric-value">${safeFixed(eval.avg_depth, 1)} steps</div>
            </div>
            <div class="metric">
                <div class="metric-label">Multi-Tool Rate</div>
                <div class="metric-value">${safeFixed((eval.multi_tool_rate || 0) * 100, 1)}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Questions</div>
                <div class="metric-value">${eval.total_questions || 0}</div>
            </div>
        `;
    } else {
        // Legacy evaluation format - use safeFixed for all numeric values
        html += `
            <div class="metric">
                <div class="metric-label">pass^5</div>
                <div class="metric-value success">${safeFixed((eval.overall_pass_5 || 0) * 100, 1)}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">pass^10</div>
                <div class="metric-value success">${safeFixed((eval.overall_pass_10 || 0) * 100, 1)}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Consensus</div>
                <div class="metric-value">${safeFixed((eval.avg_consensus_strength || 0) * 100, 1)}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Questions</div>
                <div class="metric-value">${eval.dataset_size || 0}</div>
            </div>
        `;
    }

    html += `
        </div>

        <h3 style="margin-top: 30px; margin-bottom: 15px;">By Category</h3>
        <div class="eval-metrics">
    `;

    if (eval.category_metrics) {
        for (const [category, metrics] of Object.entries(eval.category_metrics)) {
            if (isB2BEval) {
                // B2B format: metrics is an object with pass_rate, avg_score, etc.
                html += `
                    <div class="metric">
                        <div class="metric-label">${category.replace(/_/g, ' ')}</div>
                        <div style="font-size: 0.9rem; margin-top: 5px;">
                            Pass Rate: ${safeFixed((metrics.pass_rate || 0) * 100, 0)}%<br>
                            Avg Score: ${safeFixed(metrics.avg_score, 1)}
                        </div>
                    </div>
                `;
            } else {
                // Legacy format
                html += `
                    <div class="metric">
                        <div class="metric-label">${category}</div>
                        <div style="font-size: 0.9rem; margin-top: 5px;">
                            pass^5: ${safeFixed((metrics.pass_5_rate || 0) * 100, 0)}%<br>
                            pass^10: ${safeFixed((metrics.pass_10_rate || 0) * 100, 0)}%
                        </div>
                    </div>
                `;
            }
        }
    }

    html += `
        </div>

        <h3 style="margin-top: 30px; margin-bottom: 15px;">Question Results</h3>
    `;

    if (eval.question_results && eval.question_results.length > 0) {
        eval.question_results.forEach(q => {
            if (isB2BEval) {
                // B2B format - use correct field names from actual data
                const passedIcon = q.passed ? '✓' : '✗';
                const passedClass = q.passed ? 'success' : 'warning';

                // Use 'score' not 'avg_score'
                const score = q.score !== undefined ? q.score : (q.avg_score || 0);

                // Simple score tooltip (under 50 characters)
                const scoreTooltip = 'AI-scored: tools, reasoning, answer (0-100)';

                html += `
                    <div class="question-card">
                        <div class="question-header">
                            <span class="question-id">${q.question_id}</span>
                            <span class="question-category">${q.category}</span>
                        </div>
                        <div class="question-text">${escapeHtml(q.question_text || q.question || '')}</div>
                        <div style="display: flex; gap: 20px; margin-top: 10px; font-size: 0.9rem;">
                            <span class="${passedClass}">Status: ${passedIcon}</span>
                            <span title="${scoreTooltip}" style="cursor: help; border-bottom: 1px dotted #666;">
                                Score: ${safeFixed(score, 0)}/100
                            </span>
                        </div>
                    </div>
                `;
            } else {
                // Legacy format
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
                            <span>Consensus: ${safeFixed((q.consensus_strength || 0) * 100, 0)}%</span>
                        </div>
                    </div>
                `;
            }
        });
    }

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
