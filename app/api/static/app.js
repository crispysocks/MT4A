const chatDiv = document.getElementById('chat');
const input = document.getElementById('input');

async function send() {
    const message = input.value;
    if (!message) return;
    input.value = '';

    chatDiv.innerHTML += `<div class="message user"><strong>User:</strong> ${message}</div>`;

    const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({messages: [{role: 'user', content: message}]})
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    chatDiv.innerHTML += `<div class="message assistant"><strong>Assistant:</strong> <span id="assistant-response"></span></div>`;
    const responseSpan = document.getElementById('assistant-response');

    while (true) {
        const {done, value} = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        for (const line of chunk.split('\n')) {
            if (line.startsWith('data: ')) {
                try {
                    const data = JSON.parse(line.slice(6));
                    if (data.content) {
                        responseSpan.textContent += data.content;
                    }
                } catch (e) {}
            }
        }
    }
}

input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') send();
});