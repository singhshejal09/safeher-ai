"""Conversational orchestration kept separate from HTTP routes and ML code."""
from __future__ import annotations

import re
from typing import Callable

from ai_agent.model_provider import DemoModelProvider, ModelProvider

LEGAL_TERMS = re.compile(
    r"\b(rights|law|legal|complaint|police|report|protection|act|section|helpline|file a case|can i report|what can i do|my options|shebox|posh|nalsa)\b"
    r"|अधिकार|कानून|कानूनी|शिकायत|पुलिस|रिपोर्ट|हेल्पलाइन|कहाँ शिकायत|क्या अधिकार|क्या कर सकती|मदद मिलेगी"
    r"|\b(adhikaar|kanoon|shikayat|police|report kar|complaint kar|haq|kya karu|kya karoon|madad milegi)\b",
    re.I,
)
URGENT_TERMS = re.compile(
    r"\b(in danger|unsafe now|being attacked|attacking me|weapon|can't leave|cannot leave|trapped|break(?:ing)? into|forcing (?:his|her|their) way|help me now|emergency)\b"
    r"|अभी.{0,20}(?:खतरा|हमला|मार|धमकी|घुस|जबरदस्ती)|बाहर नहीं जा|तत्काल खतरा"
    r"|\babhi.{0,24}(?:khatra|danger|attack|maar|dhamki|ghus|tod|break)|bachao|maar raha",
    re.I,
)
NEGATED_URGENT = re.compile(r"\b(not in danger|no danger|safe (?:right )?now|not at risk)\b|खतरे में नहीं|अभी सुरक्षित हूँ", re.I)

FOLLOWUPS = {
    "domestic_violence": ("Are you somewhere you feel safe right now?", "क्या आप अभी ऐसी जगह हैं जहाँ सुरक्षित महसूस करती हैं?", "Kya aap abhi aisi jagah par hain jahan safe feel karti hain?"),
    "workplace_discrimination": ("Is this happening right now, or are you looking for options for something that already happened?", "क्या यह अभी हो रहा है या आप पहले हुई घटना के विकल्प जानना चाहती हैं?", "Kya yeh abhi ho raha hai ya pehle hui baat ke options dekhna chahti hain?"),
    "cyber_harassment": ("Is anyone threatening to come to you or harm you in person right now?", "क्या कोई अभी आपके पास आने या आपको नुकसान पहुँचाने की धमकी दे रहा है?", "Kya koi abhi aapke paas aane ya saamne harm karne ki dhamki de raha hai?"),
    "stalking": ("Are you somewhere you feel physically safe right now?", "क्या आप अभी शारीरिक रूप से सुरक्षित जगह पर हैं?", "Kya aap abhi physically safe jagah par hain?"),
    "harassment": ("Is this happening right now, and are you physically safe where you are?", "क्या यह अभी हो रहा है, और क्या आप जहाँ हैं वहाँ सुरक्षित हैं?", "Kya yeh abhi ho raha hai aur kya aap jahan hain wahan safe hain?"),
    "unsafe_situation": ("Is anyone in immediate danger right now, including you?", "क्या अभी कोई तत्काल खतरे में है, आप भी?", "Kya abhi koi immediate danger mein hai, aap bhi?"),
    "general_query": ("What kind of support would help most right now: immediate safety, understanding options, or finding someone to talk to?", "अभी किस तरह की मदद सबसे उपयोगी होगी: सुरक्षा, विकल्प समझना, या किसी से बात करना?", "Abhi kis tarah ki help useful hogi: safety, options samajhna, ya kisi se baat karna?"),
}


def detect_language(text: str) -> str:
    if re.search(r"[\u0900-\u097f]", text):
        return "hi"
    if re.search(r"\b(mai|main|mujhe|mere|meri|kya|nahi|nahin|ghar|pati|darr|madad|kaise|chahiye)\b", text, re.I):
        return "hinglish"
    return "en"


def is_possible_emergency(text: str, category: str) -> bool:
    # The tiny baseline classifier may label vague inputs such as "help" as
    # emergency. Only an explicit urgency cue should trigger an emergency alert.
    return bool(URGENT_TERMS.search(text)) and not NEGATED_URGENT.search(text)


class SafetyAgent:
    def __init__(self, model: ModelProvider, classify: Callable[[str], dict], rights_lookup: Callable[..., list[dict]]) -> None:
        self.model = model
        self.classify = classify
        self.rights_lookup = rights_lookup

    async def respond(self, message: str, history: list[dict[str, str]] | None = None, jurisdiction: str | None = None) -> dict:
        history = history or []
        language = detect_language(message)
        prediction = self.classify(message)
        category = prediction["predicted_category"]
        emergency = is_possible_emergency(message, category)
        if emergency:
            # Explicit urgent wording takes precedence over a low-confidence model label.
            category = "emergency"
        elif prediction.get("needs_clarification") or category == "emergency":
            # Uncertain labels and a bare emergency prediction need clarification,
            # not a confident-sounding category or emergency alert.
            category = "general_query"
        rights_related_category = category in {
            "harassment", "stalking", "domestic_violence", "cyber_harassment",
            "workplace_discrimination",
        }
        legal_question = bool(LEGAL_TERMS.search(message)) or rights_related_category
        sources = self.rights_lookup(
            category=category, jurisdiction=jurisdiction, query=message,
            language=language, limit=3,
        ) if (legal_question or emergency) and jurisdiction else []
        used_fallback = False

        if emergency:
            replies = {
                "en": "Your safety is the priority right now. If you can, move to a safer place and contact someone you trust or an appropriate official emergency service. SafeHer AI cannot contact responders or dispatch help.",
                "hi": "आपकी सुरक्षा अभी सबसे ज़रूरी है। यदि संभव हो तो सुरक्षित जगह जाएँ और किसी भरोसेमंद व्यक्ति या उचित आधिकारिक आपातकालीन सेवा से संपर्क करें। SafeHer AI सहायता भेज या सेवा को संपर्क नहीं कर सकता।",
                "hinglish": "Aapki safety abhi sabse zaroori hai. Ho sake toh safe jagah par jaayein aur kisi trusted person ya official emergency service se contact karein. SafeHer AI responders ko contact ya dispatch nahi kar sakta.",
            }
            reply = replies[language]
        elif legal_question:
            if sources:
                opening = {
                    "en": "General information from verified official sources (not legal advice):",
                    "hi": "सत्यापित आधिकारिक स्रोतों से सामान्य जानकारी (कानूनी सलाह नहीं):",
                    "hinglish": "Verified official sources se general information (legal advice nahi):",
                }[language]
                reply = opening + "\n\n" + "\n\n".join(
                    f"{source['title']}: {source.get('content') or source['summary']}" for source in sources
                )
            else:
                if not jurisdiction:
                    reply = {
                        "en": "I can help look up official information, but I need your country or region first. I won’t infer it from your language. I can’t verify which law applies until you choose a jurisdiction.",
                        "hi": "मैं आधिकारिक जानकारी खोज सकती हूँ, लेकिन पहले आपका देश या क्षेत्र जानना ज़रूरी है। मैं आपकी भाषा से स्थान का अनुमान नहीं लगाऊँगी। क्षेत्र चुने बिना लागू कानून सत्यापित नहीं कर सकती।",
                        "hinglish": "Main official information dhoondh sakti hoon, par pehle aapka country ya region chahiye. Main language se location assume nahi karungi. Jurisdiction choose kiye bina applicable law verify nahi kar sakti.",
                    }[language]
                else:
                    reply = {
                        "en": "I could not retrieve a relevant, current source from the verified official knowledge base for this question and region, so I can’t verify the legal answer. Please check the linked official resources or speak with a qualified local advisor.",
                        "hi": "इस प्रश्न और क्षेत्र के लिए सत्यापित आधिकारिक ज्ञान आधार से प्रासंगिक, वर्तमान स्रोत नहीं मिला, इसलिए मैं कानूनी उत्तर सत्यापित नहीं कर सकती। कृपया आधिकारिक संसाधन देखें या योग्य स्थानीय सलाहकार से बात करें।",
                        "hinglish": "Is question aur region ke liye verified official knowledge base se relevant, current source nahi mila, isliye main legal answer verify nahi kar sakti. Official resources check karein ya qualified local advisor se baat karein.",
                    }[language]
        else:
            try:
                reply = await self.model.generate(message=message, language=language, category=category, history=history)
            except Exception:
                # The safety flow remains available if a configured model server is down.
                used_fallback = True
                reply = await DemoModelProvider().generate(message=message, language=language, category=category, history=history)
            if not history and category in FOLLOWUPS:
                reply += "\n\n" + FOLLOWUPS[category][{"en": 0, "hi": 1, "hinglish": 2}[language]]

        return {
            "reply": reply,
            "category": category,
            "categoryLabel": category.replace("_", " ").title(),
            "language": language,
            "emergency": emergency,
            "sources": sources,
            "resources": [],
            "model": "verified-knowledge" if legal_question else ("safety-policy" if emergency else ("DemoModelProvider (fallback)" if used_fallback else self.model.__class__.__name__)),
            "disclaimer": "General information, not legal advice. SafeHer AI is not an emergency service and cannot contact or dispatch responders.",
        }
