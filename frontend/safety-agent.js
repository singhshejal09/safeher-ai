/* Triage and safety policy sit outside the swappable language-model adapter. */
window.SafeHerAgent = (() => {
  const CATEGORY = {
    emergency: { en: 'Possible immediate danger', hi: 'तत्काल खतरे की संभावना' },
    relationship: { en: 'Relationship or home safety', hi: 'रिश्ते या घर की सुरक्षा' },
    workplace: { en: 'Workplace concern', hi: 'कार्यस्थल से जुड़ी चिंता' },
    online: { en: 'Online safety or harassment', hi: 'ऑनलाइन सुरक्षा या उत्पीड़न' },
    stalking: { en: 'Stalking or unwanted contact', hi: 'पीछा करना या अनचाहा संपर्क' },
    general: { en: 'Personal safety', hi: 'व्यक्तिगत सुरक्षा' },
    unknown: { en: 'Still understanding', hi: 'स्थिति समझ रही हूँ' }
  };
  const PATTERNS = {
    emergency: /\b(right away|in danger|unsafe now|being attacked|attacking me|he(?:'s| is) here|threaten(?:ing)? me now|locked me in|weapon|can't leave|help me now|emergency)\b|अभी खतरे|अभी सुरक्षित नहीं|अभी हमला|बंद कर दिया|बाहर नहीं जा|मदद करो अभी|तत्काल खतरा|bachao|abhi khatra|abhi danger|maar raha|maarne ki dhamki/i,
    relationship: /partner|husband|boyfriend|ex-partner|relationship|at home|family member|domestic|घर|पति|साथी|परिवार|मारता|धमकी|ghar par|pati|partner/i,
    workplace: /workplace|office|boss|manager|colleague|coworker|काम की जगह|दफ्तर|बॉस|सहकर्मी|kaam ki jagah|office me/i,
    online: /online|internet|social media|message(?:s|d)?|photo|image|account|cyber|सोशल मीडिया|ऑनलाइन|तस्वीर|फोटो|मैसेज|खाता|online par|photo share/i,
    stalking: /follow(?:ing|ed)? me|stalk(?:ing|ed)?|keeps showing up|won't stop contacting|unwanted contact|पीछा|बार-बार संपर्क|संपर्क नहीं रोक|mera peecha|baar baar call/i
  };
  const FOLLOWUPS = {
    relationship: { en: 'To help me understand: are you safe where you are right now?', hi: 'बेहतर समझने के लिए: क्या आप अभी जहाँ हैं वहाँ सुरक्षित हैं?' },
    workplace: { en: 'Is this happening right now, or are you looking for options for something that already happened?', hi: 'क्या यह अभी हो रहा है, या आप पहले हुई घटना के विकल्प जानना चाहती हैं?' },
    online: { en: 'Is anyone threatening to come to you or harm you in person right now?', hi: 'क्या कोई अभी आपके पास आने या आपको नुकसान पहुँचाने की धमकी दे रहा है?' },
    stalking: { en: 'Are you somewhere you feel physically safe right now?', hi: 'क्या आप अभी ऐसी जगह हैं जहाँ आपको शारीरिक रूप से सुरक्षित महसूस हो?' },
    general: { en: 'Is anyone in immediate danger right now, including you?', hi: 'क्या अभी कोई तत्काल खतरे में है, आप भी?' },
    unknown: { en: 'What kind of support would help most right now: immediate safety, understanding options, or finding someone to talk to?', hi: 'अभी किस तरह की मदद सबसे उपयोगी होगी: तुरंत सुरक्षा, विकल्प समझना, या किसी से बात करना?' }
  };
  const HINGLISH_FOLLOWUPS = {
    relationship: 'Mujhe behtar samajhne ke liye: kya aap abhi jahan hain, wahan safe feel kar rahi hain?',
    workplace: 'Kya yeh abhi ho raha hai, ya pehle hui baat ke options dekhna chahti hain?',
    online: 'Kya koi abhi aapke paas aane ya saamne harm karne ki dhamki de raha hai?',
    stalking: 'Kya aap abhi aisi jagah par hain jahan physically safe feel karti hain?',
    general: 'Kya abhi koi immediate danger mein hai, aap bhi?',
    unknown: 'Abhi kis tarah ki help useful hogi: immediate safety, options samajhna, ya kisi se baat karna?'
  };
  const HINGLISH = /\b(mai|main|mujhe|mere|meri|kya|nahi|nahin|ghar|pati|darr|dar|madad|surakshit|safe nahi|pareshan|kaise|chahiye)\b/i;
  const LEGAL = /\b(rights|law|legal|complaint|police|report|protection order|workplace policy)\b|अधिकार|कानून|शिकायत|पुलिस|रिपोर्ट/i;
  const NEGATED_EMERGENCY = /\b(not in danger|not in immediate danger|no danger|safe (?:right )?now|not at risk)\b|खतरे में नहीं|अभी सुरक्षित हूँ/i;
  const AFFIRMATIVE = /^\s*(yes|yeah|yep|i am|i do|he is|she is|they are|haan|han|ha|जी|हाँ|हां|हाँ जी|सही|हो|हो रहा|हो रही)(\b|[.!?,\s])/i;
  const NEGATIVE = /^\s*(no|nope|not really|i am not|i'm not|not safe|nah|nahi|nahin|नहीं|नही|नहीं जी)(\b|[.!?,\s])/i;
  function languageOf(text) {
    if (/[\u0900-\u097F]/.test(text)) return 'hi';
    if (HINGLISH.test(text)) return 'hinglish';
    return 'en';
  }
  function classify(text) {
    if (PATTERNS.emergency.test(text) && !NEGATED_EMERGENCY.test(text)) return { category: 'emergency', confidence: 'high' };
    for (const category of ['relationship', 'workplace', 'online', 'stalking']) {
      if (PATTERNS[category].test(text)) return { category, confidence: 'medium' };
    }
    if (text.trim().length > 0) return { category: 'general', confidence: 'low' };
    return { category: 'unknown', confidence: 'low' };
  }
  function isEmergency(text) { return PATTERNS.emergency.test(text) && !NEGATED_EMERGENCY.test(text); }
  function humanCategory(category, language) { return CATEGORY[category]?.[language === 'hi' ? 'hi' : 'en'] || CATEGORY.unknown.en; }
  function followup(category, language) {
    const phrasing = FOLLOWUPS[category] || FOLLOWUPS.unknown;
    if (language === 'hinglish') return HINGLISH_FOLLOWUPS[category] || HINGLISH_FOLLOWUPS.unknown;
    return phrasing[language === 'hi' ? 'hi' : 'en'];
  }
  class SafetyAgent {
    constructor({ model, knowledgeBase, resources = window.SAFEHER_CONFIG || {} }) {
      this.model = model;
      this.knowledgeBase = knowledgeBase;
      this.resources = resources;
      this.asked = new Set();
      this.pendingSafetyConfirmation = null;
      this.pendingLanguage = 'en';
    }
    reset() { this.asked.clear(); this.pendingSafetyConfirmation = null; this.pendingLanguage = 'en'; }
    async respond(message, history = []) {
      let language = languageOf(message);
      const pending = this.pendingSafetyConfirmation;
      const confirmedEmergency = (pending === 'danger' && AFFIRMATIVE.test(message)) || (pending === 'safe' && NEGATIVE.test(message));
      if (confirmedEmergency) language = this.pendingLanguage;
      this.pendingSafetyConfirmation = null;
      const triage = confirmedEmergency ? { category: 'emergency', confidence: 'high' } : classify(message);
      const emergency = confirmedEmergency || isEmergency(message);
      const legalQuestion = LEGAL.test(message);
      const rights = legalQuestion ? this.knowledgeBase.search('*', language) : this.knowledgeBase.search(triage.category, language);
      const context = { message, category: triage.category, language, history: history.slice(-6), emergency, verifiedSources: rights };
      let reply;
      try {
        reply = emergency || legalQuestion ? '' : await this.model.generate(context);
      } catch {
        reply = language === 'hi'
          ? 'मैंने आपकी बात समझने की कोशिश की है। आप चाहें तो भरोसेमंद व्यक्ति से संपर्क करें; मैं एक छोटा अगला कदम सोचने में मदद कर सकती हूँ।'
          : 'I’m having trouble generating a response right now. You can still explore the safety guidance and verified resources on this page.';
      }
      if (emergency) {
        reply = language === 'hi'
          ? 'आपकी सुरक्षा अभी सबसे ज़रूरी है। यदि संभव हो तो सुरक्षित जगह जाएँ और किसी भरोसेमंद व्यक्ति या सत्यापित स्थानीय आपातकालीन सेवा से संपर्क करें।'
          : language === 'hinglish'
            ? 'Aapki safety abhi sabse zaroori hai. Ho sake toh safe jagah par jaayein aur kisi trusted person ya verified local emergency service se contact karein.'
            : 'Your safety is the priority right now. If you can, move to a safer place and contact someone you trust or a verified local emergency service.';
      } else if (legalQuestion) {
        reply = rights.length
          ? rights.map(entry => `${entry.title}: ${entry.summary}`).join('\n\n')
          : language === 'hi' ? 'इस विषय के लिए अभी कोई सत्यापित स्थानीय कानूनी स्रोत उपलब्ध नहीं है। मैं कानूनी निष्कर्ष नहीं दे सकती।' : language === 'hinglish' ? 'Is topic ke liye abhi verified local legal source available nahi hai. Main legal conclusion nahi de sakti.' : 'I don’t have a verified local legal source for this topic yet, so I can’t provide a legal conclusion.';
      } else if (!emergency && triage.category !== 'general' && triage.category !== 'unknown' && !this.asked.has(triage.category)) {
        this.asked.add(triage.category);
        if (triage.category === 'relationship' || triage.category === 'stalking') {
          this.pendingSafetyConfirmation = 'safe';
          this.pendingLanguage = language;
        } else if (triage.category === 'online') {
          this.pendingSafetyConfirmation = 'danger';
          this.pendingLanguage = language;
        }
        reply = `${reply}\n\n${followup(triage.category, language)}`;
      } else if ((triage.category === 'general' || triage.category === 'unknown') && history.length === 0 && !this.asked.has('general')) {
        this.asked.add('general');
        this.pendingSafetyConfirmation = 'danger';
        this.pendingLanguage = language;
        reply = `${reply}\n\n${followup(triage.category, language)}`;
      }
      return {
        reply,
        category: triage.category,
        categoryLabel: humanCategory(triage.category, language),
        language,
        emergency,
        sources: rights,
        resources: emergency ? [...(this.resources.emergencyResources || []), ...(this.resources.nearbyResources || [])] : []
      };
    }
  }
  return { SafetyAgent, classify, isEmergency, languageOf, humanCategory };
})();
