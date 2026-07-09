const chat = document.getElementById('chat');
const form = document.getElementById('composer');
const input = document.getElementById('question');
const sendBtn = document.getElementById('send-btn');

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function addMessage(role, text, sources) {
  const msg = document.createElement('div');
  msg.className = `msg ${role}`;

  const label = document.createElement('div');
  label.className = 'msg-label';
  label.textContent = role === 'user' ? 'you' : role === 'error' ? 'error' : 'advisor';
  msg.appendChild(label);

  const body = document.createElement('div');
  body.className = 'msg-body';
  body.innerHTML = escapeHtml(text);
  msg.appendChild(body);

  if (sources && sources.length > 0) {
    const src = document.createElement('div');
    src.className = 'sources';
    src.innerHTML = 'Sources: ' + sources
      .map(s => `<span>${escapeHtml(s.book)} p.${escapeHtml(String(s.page))}</span>`)
      .join('');
    msg.appendChild(src);
  }

  chat.appendChild(msg);
  chat.scrollTop = chat.scrollHeight;
  return msg;
}

async function sendQuestion(question) {
  addMessage('user', question);
  input.value = '';
  input.style.height = 'auto';
  sendBtn.disabled = true;

  const thinkingMsg = addMessage('system', 'thinking...');
  thinkingMsg.classList.add('thinking');

  try {
    const res = await fetch('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();

    thinkingMsg.remove();

    if (!res.ok) {
      addMessage('error', data.error || 'Something went wrong.');
    } else {
      addMessage('assistant', data.answer, data.sources);
    }
  } catch (err) {
    thinkingMsg.remove();
    addMessage('error', 'Could not reach the server: ' + err.message);
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

form.addEventListener('submit', (e) => {
  e.preventDefault();
  const q = input.value.trim();
  if (!q) return;
  sendQuestion(q);
});

input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    form.requestSubmit();
  }
});

input.addEventListener('input', () => {
  input.style.height = 'auto';
  input.style.height = Math.min(input.scrollHeight, 160) + 'px';
});
