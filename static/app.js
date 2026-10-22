const form = document.querySelector('#question-form');
const input = document.querySelector('#question');
const conversation = document.querySelector('#conversation');
const sendButton = document.querySelector('#send-button');
const voiceButton = document.querySelector('#voice-button');
const voiceStatus = document.querySelector('#voice-status');

function addMessage(text, kind, meta = '') {
  const bubble = document.createElement('div');
  bubble.className = `message ${kind}`;
  const content = document.createElement('span');
  content.className = 'message-text';
  content.textContent = text;
  bubble.appendChild(content);
  conversation.appendChild(bubble);
  if (meta) {
    const details = document.createElement('div');
    details.className = 'message-meta';
    details.textContent = meta;
    conversation.appendChild(details);
  }
  conversation.scrollTop = conversation.scrollHeight;
  return bubble;
}

async function ask(question) {
  addMessage(question, 'user');
  input.value = '';
  sendButton.disabled = true;
  const pending = addMessage('Looking that up…', 'bot');
  try {
    const response = await fetch('/api/ask', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Unable to get an answer.');
    pending.querySelector('.message-text').textContent = result.answer;
    if (result.category) {
      const details = document.createElement('div');
      details.className = 'message-meta';
      details.textContent = `Topic: ${result.category}`;
      pending.after(details);
    }
  } catch (error) {
    pending.textContent = error.message || 'Something went wrong. Please try again.';
  } finally {
    sendButton.disabled = false;
    input.focus();
    conversation.scrollTop = conversation.scrollHeight;
  }
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (question) ask(question);
});

document.querySelectorAll('.suggestion').forEach((button) => {
  button.addEventListener('click', () => ask(button.textContent.trim()));
});

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (voiceButton) {
  if (!SpeechRecognition) {
    voiceButton.addEventListener('click', () => {
      voiceStatus.textContent = 'Voice typing is not available in this browser. Try Chrome or Edge.';
    });
  } else {
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-IN';
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.onstart = () => {
      voiceButton.classList.add('listening');
      voiceButton.setAttribute('aria-label', 'Stop voice typing');
      voiceStatus.textContent = 'Listening… speak your question.';
    };
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript.trim();
      input.value = `${input.value.trim()} ${transcript}`.trim();
      voiceStatus.textContent = 'Your speech is in the question box. Edit it if needed, then press Ask.';
      input.focus();
    };
    recognition.onerror = (event) => {
      voiceStatus.textContent = event.error === 'not-allowed'
        ? 'Microphone access is blocked. Allow microphone access in your browser settings.'
        : 'Could not hear that. Click the microphone and try again.';
    };
    recognition.onend = () => {
      voiceButton.classList.remove('listening');
      voiceButton.setAttribute('aria-label', 'Dictate your question');
      if (voiceStatus.textContent === 'Listening… speak your question.') voiceStatus.textContent = '';
    };
    voiceButton.addEventListener('click', () => {
      if (voiceButton.classList.contains('listening')) recognition.stop();
      else {
        voiceStatus.textContent = '';
        recognition.start();
      }
    });
  }
}

document.querySelectorAll('.topic').forEach((button) => {
  button.addEventListener('click', () => {
    const prompts = {
      Eligibility: 'What are the eligibility requirements?',
      Courses: 'Which courses are available?',
      Fees: 'What are the tuition fees and scholarships?',
      Application: 'How do I apply for admission? What are the application steps?',
      Documents: 'Which documents are required?',
      'Important Dates': 'When is the application deadline?',
      Policies: 'What are the admission policies?'
    };
    ask(prompts[button.dataset.topic] || `Tell me about ${button.dataset.topic}.`);
  });
});

document.querySelectorAll('.guide-ask').forEach((button) => {
  button.addEventListener('click', () => {
    const questions = {
      Application: 'How do I apply for admission?',
      Fees: 'What are the tuition fees and scholarships?',
      'Important Dates': 'When is the application deadline?',
      Documents: 'Which documents are required?',
      Policies: 'What are the admission policies?'
    };
    ask(questions[button.dataset.topic] || `Tell me about ${button.dataset.topic}.`);
  });
});

const campusDialog = document.querySelector('#campus-dialog');
if (campusDialog) {
  const dialogImage = document.querySelector('#campus-dialog-image');
  const dialogCaption = document.querySelector('#campus-dialog-caption');
  document.querySelectorAll('.campus-card').forEach((card) => {
    card.addEventListener('click', () => {
      dialogImage.src = card.dataset.image;
      dialogImage.alt = card.dataset.alt;
      dialogCaption.textContent = card.dataset.title;
      campusDialog.showModal();
    });
  });
  document.querySelector('.campus-dialog-close').addEventListener('click', () => campusDialog.close());
  campusDialog.addEventListener('click', (event) => {
    if (event.target === campusDialog) campusDialog.close();
  });
}

document.querySelectorAll('.course-ask').forEach((button) => {
  button.addEventListener('click', () => ask(`What is the fee for ${button.dataset.course}?`));
});
