let currentConversationId = null;
let isStreaming = false;

const chatEl = document.getElementById('chat');
const chatEmpty = document.getElementById('chat-empty');
const inputEl = document.getElementById('input');
const sendBtn = document.getElementById('send');
const sessionListEl = document.getElementById('session-list');
const newChatBtn = document.getElementById('new-chat-btn');

// 发送消息
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

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                conversation_id: currentConversationId,
                message: message
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const {done, value} = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, {stream: true});
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

// 添加消息
function appendMessage(role, text) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = `<div class="role">${role === 'user' ? 'You' : 'Assistant'}</div>`;
    div.appendChild(document.createTextNode(text));
    chatEl.appendChild(div);
    scrollToBottom();
    return div;
}

// 滚动到底部
function scrollToBottom() {
    chatEl.scrollTop = chatEl.scrollHeight;
}

// 显示加载动画
function showLoading(container) {
    const dots = document.createElement('div');
    dots.className = 'loading-dots';
    dots.innerHTML = '<span></span><span></span><span></span>';
    container.appendChild(dots);
    scrollToBottom();
}

// 隐藏加载动画
function hideLoading(container) {
    const dots = container.querySelector('.loading-dots');
    if (dots) dots.remove();
}

// 隐藏空状态
function hideEmpty() {
    if (chatEmpty) chatEmpty.style.display = 'none';
}

// 显示空状态
function showEmpty() {
    if (chatEmpty) chatEmpty.style.display = 'flex';
}

// 加载会话列表
async function loadSessions() {
    try {
        const response = await fetch('/api/sessions');
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
    } catch (e) {
        console.error('Failed to load sessions:', e);
    }
}

// 加载指定会话
async function loadSession(id) {
    if (isStreaming) return;
    
    currentConversationId = id;
    chatEl.innerHTML = '<div id="chat-empty">开始新对话</div>';
    
    try {
        const response = await fetch(`/api/sessions/${id}`);
        const session = await response.json();
        
        if (session.messages && session.messages.length > 0) {
            hideEmpty();
            session.messages.forEach(msg => {
                const content = typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content);
                appendMessage(msg.role, content);
            });
        } else {
            showEmpty();
        }
    } catch (e) {
        console.error('Failed to load session:', e);
    }
    
    loadSessions();
}

// 新对话
newChatBtn.onclick = () => {
    if (isStreaming) return;
    currentConversationId = null;
    chatEl.innerHTML = '<div id="chat-empty">开始新对话</div>';
    showEmpty();
    loadSessions();
};

// 发送按钮
sendBtn.onclick = send;

// Enter 发送，Shift+Enter 换行
inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        send();
    }
});

// 初始加载
loadSessions();
