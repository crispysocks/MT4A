const token = localStorage.getItem('token');
const role = localStorage.getItem('role') || 'guest';
const THEME_COLORS = { student: '#2563eb', employee: '#16a34a', guest: '#6b7280' };

let currentConversationId = null;
let isStreaming = false;

const chatEl = document.getElementById('chat');
const chatEmpty = document.getElementById('chat-empty');
const inputEl = document.getElementById('input');
const sendBtn = document.getElementById('send');
const sessionListEl = document.getElementById('session-list');
const newChatBtn = document.getElementById('new-chat-btn');
const topbar = document.getElementById('topbar');
const roleLabel = document.getElementById('role-label');
const guestBanner = document.getElementById('guest-banner');

const themeColor = THEME_COLORS[role] || '#6b7280';
topbar.style.background = themeColor;
sendBtn.style.background = themeColor;

if (!token) {
    roleLabel.textContent = '客服助手 (游客)';
    document.getElementById('logout-btn').style.display = 'none';
    guestBanner.style.display = 'block';
} else if (role === 'student') {
    roleLabel.textContent = '学生助手';
} else if (role === 'employee') {
    roleLabel.textContent = '企业助手';
}

function logout() {
    fetch('/api/auth/logout', { method: 'POST' });
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    window.location.href = '/login';
}

async function send() {
    const message = inputEl.value.trim();
    if (!message || isStreaming) return;

    inputEl.value = '';
    hideEmpty();
    appendMessage('user', message);

    isStreaming = true;
    sendBtn.disabled = true;

    const assistantDiv = appendMessage('assistant', '');
    showLoading(assistantDiv);
    let assistantText = '';

    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = 'Bearer ' + token;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST', headers,
            body: JSON.stringify({
                conversation_id: currentConversationId,
                message: message
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            for (const line of chunk.split('\n')) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.type === 'conversation_id') {
                            currentConversationId = data.conversation_id;
                        } else if (data.type === 'content') {
                            hideLoading(assistantDiv);
                            assistantText += data.content;
                            assistantDiv.textContent = assistantText;
                            scrollToBottom();
                        } else if (data.type === 'error') {
                            assistantDiv.textContent = `Error: ${data.content}`;
                        }
                    } catch (e) {}
                }
            }
        }
    } catch (e) {
        assistantDiv.textContent = `Error: ${e.message}`;
    } finally {
        isStreaming = false;
        sendBtn.disabled = false;
        loadSessions();
    }
}

function appendMessage(role, text) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = `<div class="role">${role === 'user' ? 'You' : 'Assistant'}</div>`;
    div.appendChild(document.createTextNode(text));
    chatEl.appendChild(div);
    scrollToBottom();
    return div;
}

function scrollToBottom() { chatEl.scrollTop = chatEl.scrollHeight; }

function showLoading(container) {
    const dots = document.createElement('div');
    dots.className = 'loading-dots';
    dots.innerHTML = '<span></span><span></span><span></span>';
    container.appendChild(dots);
    scrollToBottom();
}

function hideLoading(container) {
    const dots = container.querySelector('.loading-dots');
    if (dots) dots.remove();
}

function hideEmpty() { if (chatEmpty) chatEmpty.style.display = 'none'; }
function showEmpty() { if (chatEmpty) chatEmpty.style.display = 'flex'; }

async function loadSessions() {
    try {
        const headers = {};
        if (token) headers['Authorization'] = 'Bearer ' + token;
        const response = await fetch('/api/sessions', { headers });
        const sessions = await response.json();
        sessionListEl.innerHTML = '';
        if (sessions.length === 0) {
            sessionListEl.innerHTML = '<div class="empty-state">暂无对话</div>';
            return;
        }
        sessions.forEach(s => {
            const div = document.createElement('div');
            div.className = `session-item ${s.id === currentConversationId ? 'active' : ''}`;
            div.textContent = `对话 ${s.id.slice(0, 8)}`;
            div.onclick = () => loadSession(s.id);
            sessionListEl.appendChild(div);
        });
    } catch (e) { console.error('Failed to load sessions:', e); }
}

async function loadSession(id) {
    if (isStreaming) return;
    currentConversationId = id;
    chatEl.innerHTML = '<div id="chat-empty">开始新对话</div>';
    try {
        const headers = {};
        if (token) headers['Authorization'] = 'Bearer ' + token;
        const response = await fetch(`/api/sessions/${id}`, { headers });
        const session = await response.json();
        if (session.messages && session.messages.length > 0) {
            hideEmpty();
            session.messages.forEach(msg => {
                const content = typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content);
                appendMessage(msg.role, content);
            });
        } else { showEmpty(); }
    } catch (e) { console.error('Failed to load session:', e); }
    loadSessions();
}

newChatBtn.onclick = () => {
    if (isStreaming) return;
    currentConversationId = null;
    chatEl.innerHTML = '<div id="chat-empty">开始新对话</div>';
    showEmpty();
    loadSessions();
};

sendBtn.onclick = send;
inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
});

loadSessions();
