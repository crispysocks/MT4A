let currentConversationId = null;

const chatDiv = document.getElementById('chat');
const input = document.getElementById('input');

async function send() {
    const message = input.value.trim();
    if (!message) return;
    input.value = '';

    // 显示用户消息
    appendMessage('user', message);

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
    
    let assistantText = '';
    const assistantDiv = appendMessage('assistant', '');

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
                        assistantText += data.content;
                        assistantDiv.querySelector('.content').textContent = assistantText;
                    } else if (data.type === 'done') {
                        loadSessions();
                    } else if (data.type === 'error') {
                        assistantDiv.querySelector('.content').textContent = `Error: ${data.content}`;
                    }
                } catch (e) {}
            }
        }
    }
}

function appendMessage(role, text) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = `<strong>${role === 'user' ? 'You' : 'Assistant'}:</strong> <span class="content">${text}</span>`;
    chatDiv.appendChild(div);
    chatDiv.scrollTop = chatDiv.scrollHeight;
    return div;
}

async function loadSessions() {
    const response = await fetch('/api/sessions');
    const sessions = await response.json();
    
    const sidebar = document.getElementById('sidebar');
    sidebar.innerHTML = '<h3>Conversations</h3>';
    
    sessions.forEach(s => {
        const div = document.createElement('div');
        div.className = `session-item ${s.id === currentConversationId ? 'active' : ''}`;
        div.textContent = `Conversation ${s.id.slice(0, 8)}`;
        div.onclick = () => loadSession(s.id);
        sidebar.appendChild(div);
    });
    
    const newBtn = document.createElement('button');
    newBtn.textContent = 'New Conversation';
    newBtn.onclick = () => {
        currentConversationId = null;
        chatDiv.innerHTML = '';
        loadSessions();
    };
    sidebar.appendChild(newBtn);
}

async function loadSession(id) {
    currentConversationId = id;
    chatDiv.innerHTML = '';
    
    const response = await fetch(`/api/sessions/${id}`);
    const session = await response.json();
    
    if (session.messages) {
        session.messages.forEach(msg => {
            const content = typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content);
            appendMessage(msg.role, content);
        });
    }
    
    loadSessions();
}

input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') send();
});

// 初始加载
loadSessions();
