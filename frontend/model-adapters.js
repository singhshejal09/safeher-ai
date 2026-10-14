/* Provider boundary. Keep provider credentials on a server, never in browser code. */
window.SafeHerModels = (() => {
  class ModelAdapter {
    async generate(_input) { throw new Error('Implement generate(input) in a model adapter.'); }
  }

  class LocalDemoAdapter extends ModelAdapter {
    async generate({ message, language }) {
      const text = String(message || '').toLowerCase();
      if (language === 'hi') return 'मैं सुन रही हूँ। आपको अभी सब कुछ तय करने की ज़रूरत नहीं है। क्या आप चाहेंगी कि हम एक छोटा, सुरक्षित अगला कदम सोचें?';
      if (language === 'hinglish') return 'Main sun rahi hoon. Aapko abhi sab kuch decide karne ki zaroorat nahi hai. Kya hum ek chhota, safe next step saath sochen?';
      if (/option|help|not sure|don't know|confus/.test(text)) return 'It can be hard to know where to start. You can take this one step at a time. What would feel most useful right now?';
      return 'Thank you for telling me. You deserve support, and you can choose what happens next. What feels most important to focus on right now?';
    }
  }

  // A future same-origin backend can implement this contract without changing the agent.
  // The server should perform authentication, model access, privacy controls, and validation.
  class BackendAdapter extends ModelAdapter {
    constructor(endpoint = '/api/agent') { super(); this.endpoint = endpoint; }
    async generate(input) {
      const response = await fetch(this.endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(input) });
      if (!response.ok) throw new Error(`Agent service returned ${response.status}`);
      const result = await response.json();
      if (typeof result.reply !== 'string') throw new Error('Agent service response must include a reply.');
      return result.reply;
    }
  }
  return { ModelAdapter, LocalDemoAdapter, BackendAdapter };
})();
