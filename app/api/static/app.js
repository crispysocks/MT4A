// ── Auth & Theme ──
const token = localStorage.getItem('token');
const role = localStorage.getItem('role') || 'guest';

const THEME = {
    student: { bg: '#1e3a8a', accent: '#1e3a8a', accent2: '#2563eb', label: '学生助手' },
    employee: { bg: '#064e3b', accent: '#047857', accent2: '#059669', label: '企业助手' },
    guest: { bg: '#334155', accent: '#475569', accent2: '#64748b', label: '客服助手' },
};

const theme = THEME[role] || THEME.guest;

// ── DOM ──
const chatEl = document.getElementById('chat');
const chatEmpty = document.getElementById('chat-empty');
const inputEl = document.getElementById('input');
const sendBtn = document.getElementById('send');
const sessionListEl = document.getElementById('session-list');
const newChatBtn = document.getElementById('new-chat-btn');
const topbar = document.getElementById('topbar');
const roleLabel = document.getElementById('role-label');
const guestBanner = document.getElementById('guest-banner');

let currentConversationId = null;
let isStreaming = false;

// ── Apply Theme ──
topbar.style.background = `linear-gradient(135deg, ${theme.bg}, ${theme.accent2})`;
sendBtn.style.background = theme.accent;
sendBtn.style.setProperty('--send-hover', theme.accent2);

const styleSheet = document.createElement('style');
styleSheet.textContent = `
    #send:hover { background: ${theme.accent2} !important; }
    .session-item.active { background: ${theme.accent} !important; }
    #input:focus { border-color: ${theme.accent} !important; box-shadow: 0 0 0 3px ${theme.accent}15 !important; }
`;
document.head.appendChild(styleSheet);

// ── UI Labels ──
if (!token) {
    roleLabel.textContent = '客服助手（游客）';
    document.getElementById('logout-btn').style.display = 'none';
    guestBanner.style.display = 'block';
} else {
    roleLabel.textContent = theme.label;
}

// ── Logout ──
function logout() {
    fetch('/api/auth/logout', { method: 'POST' });
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    window.location.href = '/login';
}

// ── Auto-resize textarea ──
inputEl.addEventListener('input', () => {
    inputEl.style.height = 'auto';
    inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';
});

// ── Send ──
async function send() {
    const message = inputEl.value.trim();
    if (!message || isStreaming) return;

    inputEl.value = '';
    inputEl.style.height = 'auto';
    hideEmpty();
    appendMessage('user', message);

    isStreaming = true;
    sendBtn.disabled = true;
    sendBtn.textContent = '...';

    const assistantDiv = appendMessage('assistant', '');
    showLoading(assistantDiv);
    let assistantText = '';

    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = 'Bearer ' + token;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST', headers,
            body: JSON.stringify({ conversation_id: currentConversationId, message })
        });

        if (!response.ok && response.status === 401) {
            localStorage.removeItem('token');
            localStorage.removeItem('role');
            window.location.href = '/login';
            return;
        }

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
                            hideLoading(assistantDiv);
                            assistantDiv.innerHTML = `<span style="color:#dc2626;font-size:13px;">${data.content}</span>`;
                        }
                    } catch (e) {}
                }
            }
        }
    } catch (e) {
        hideLoading(assistantDiv);
        assistantDiv.innerHTML = `<span style="color:#dc2626;font-size:13px;">连接中断，请重试</span>`;
    } finally {
        isStreaming = false;
        sendBtn.disabled = false;
        sendBtn.textContent = '发送';
        loadSessions();
    }
}

// ── Messages ──
function appendMessage(role, text) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    const label = role === 'user' ? '我' : theme.label;
    div.innerHTML = `<div class="role-tag">${label}</div>`;
    const contentSpan = document.createElement('span');
    contentSpan.textContent = text;
    div.appendChild(contentSpan);
    chatEl.appendChild(div);
    scrollToBottom();
    return contentSpan;
}

function scrollToBottom() {
    chatEl.scrollTop = chatEl.scrollHeight;
}

// ── Loading ──
function showLoading(container) {
    const dots = document.createElement('div');
    dots.className = 'loading-indicator';
    dots.innerHTML = '<span></span><span></span><span></span>';
    container.appendChild(dots);
}
function hideLoading(container) {
    const dots = container.querySelector('.loading-indicator');
    if (dots) dots.remove();
}

// ── Empty state ──
function hideEmpty() { if (chatEmpty) chatEmpty.style.display = 'none'; }
function showEmpty() { if (chatEmpty) chatEmpty.style.display = 'flex'; }

// ── Sessions ──
async function loadSessions() {
    try {
        const headers = {};
        if (token) headers['Authorization'] = 'Bearer ' + token;
        const resp = await fetch('/api/sessions', { headers });
        const sessions = await resp.json();
        sessionListEl.innerHTML = '';
        if (!Array.isArray(sessions) || sessions.length === 0) {
            sessionListEl.innerHTML = '<div class="empty-state">暂无对话记录</div>';
            return;
        }
        sessions.forEach(s => {
            const div = document.createElement('div');
            div.className = `session-item${s.id === currentConversationId ? ' active' : ''}`;
            const date = s.updated_at ? new Date(s.updated_at).toLocaleDateString('zh-CN') : '';
            div.textContent = date ? `${date} · ${s.id.slice(0, 6)}` : `对话 ${s.id.slice(0, 8)}`;
            div.title = `ID: ${s.id}`;
            div.onclick = () => loadSession(s.id);
            sessionListEl.appendChild(div);
        });
    } catch (e) { console.error('Sessions:', e); }
}

async function loadSession(id) {
    if (isStreaming) return;
    currentConversationId = id;
    chatEl.innerHTML = '<div id="chat-empty"><div class="icon"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 2v4m0 12v4M2 12h4m12 0h4"/><circle cx="12" cy="12" r="8" opacity="0.5"/></svg></div><div class="title">加载中...</div></div>';
    try {
        const headers = {};
        if (token) headers['Authorization'] = 'Bearer ' + token;
        const resp = await fetch(`/api/sessions/${id}`, { headers });
        const session = await resp.json();
        chatEl.innerHTML = '';
        if (session.messages && session.messages.length > 0) {
            session.messages.forEach(msg => {
                let content = typeof msg.content === 'string'
                    ? msg.content
                    : (Array.isArray(msg.content)
                        ? msg.content.map(b => b.text || '').join('').slice(0, 500)
                        : String(msg.content));
                appendMessage(msg.role, content);
            });
        } else {
            chatEl.innerHTML = '<div id="chat-empty"><div class="icon"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 2v4m0 12v4M2 12h4m12 0h4"/><circle cx="12" cy="12" r="8" opacity="0.5"/></svg></div><div class="title">开始新对话</div><div class="hint">输入消息，智能助手即刻响应</div></div>';
        }
    } catch (e) { console.error('Load session:', e); }
    loadSessions();
}

// ── New Chat ──
newChatBtn.onclick = () => {
    if (isStreaming) return;
    currentConversationId = null;
    chatEl.innerHTML = '<div id="chat-empty"><div class="icon"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 2v4m0 12v4M2 12h4m12 0h4"/><circle cx="12" cy="12" r="8" opacity="0.5"/></svg></div><div class="title">开始新对话</div><div class="hint">输入消息，智能助手即刻响应</div></div>';
    loadSessions();
};

// ── Events ──
sendBtn.onclick = send;
inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
});

// ── Init ──
loadSessions();
