// AI replies and error text are untrusted — always escape before inserting.
function escapeChatHtml(value) {
    return String(value == null ? '' : value)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function sendChatMessage(chapterId) {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if (!text || !chapterId) return;
    
    const chatHistory = document.getElementById('chatHistory');
    
    // Add user message to UI
    chatHistory.innerHTML += `
        <div class="chat-msg user-msg">
            <div class="msg-bubble user-bubble">
                ${escapeChatHtml(text)}
            </div>
            <div class="msg-avatar user-avatar">👤</div>
        </div>
    `;
    
    input.value = '';
    chatHistory.scrollTop = chatHistory.scrollHeight;
    
    // Add typing indicator
    const typingId = 'typing-' + Date.now();
    chatHistory.innerHTML += `
        <div id="${typingId}" class="chat-msg">
            <div class="msg-avatar ai-avatar">🤖</div>
            <div class="msg-bubble ai-bubble" style="display: flex; align-items: center; justify-content: center; width: 60px;">
                <ion-icon name="ellipsis-horizontal" class="animate-pulse" style="font-size: 1.5rem;"></ion-icon>
            </div>
        </div>
    `;
    chatHistory.scrollTop = chatHistory.scrollHeight;
    
    // API Call to /api/chat
    fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chapterId: chapterId, message: text })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById(typingId).remove();
        if (data.success) {
            chatHistory.innerHTML += `
                <div class="chat-msg">
                    <div class="msg-avatar ai-avatar">🤖</div>
                    <div class="msg-bubble ai-bubble">
                        ${escapeChatHtml(data.reply).replace(/\n/g, '<br>')}
                    </div>
                </div>
            `;
        } else {
            chatHistory.innerHTML += `
                <div class="chat-msg">
                    <div class="msg-avatar" style="background: #ef4444; color: white;">❌</div>
                    <div class="msg-bubble" style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3);">
                        Oops! ${escapeChatHtml(data.error || 'Network error. Try again!')}
                    </div>
                </div>
            `;
        }
        chatHistory.scrollTop = chatHistory.scrollHeight;
    })
    .catch(err => {
        document.getElementById(typingId).remove();
        chatHistory.innerHTML += `
            <div class="chat-msg">
                <div class="msg-avatar" style="background: #ef4444; color: white;">❌</div>
                <div class="msg-bubble" style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3);">
                    Oops! Connection failed. Please check your internet.
                </div>
            </div>
        `;
        chatHistory.scrollTop = chatHistory.scrollHeight;
    });
}

// Allow Enter key to send chat
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('chatInput');
    if (input) {
        input.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                const btn = document.querySelector('button[onclick^="sendChatMessage"]');
                if (btn) btn.click();
            }
        });
    }
});
