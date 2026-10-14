"""Non-persisting complaint organization guidance."""
GUIDANCE = {
    "en": [
        "Start with what feels safe; you can pause or change direction at any time.",
        "If useful and safe, privately note what happened and when. You do not need to create a record to deserve help.",
        "Ask a verified local support service or qualified advisor about the process and options where you live.",
    ],
    "hi": [
        "वही कदम चुनें जो आपको सुरक्षित लगे; आप कभी भी रुक सकती हैं या दिशा बदल सकती हैं।",
        "यदि सुरक्षित और उपयोगी लगे, तो घटना और समय को निजी रूप से नोट करें। सहायता पाने के लिए रिकॉर्ड बनाना ज़रूरी नहीं है।",
        "अपने क्षेत्र में प्रक्रिया और विकल्प जानने के लिए सत्यापित स्थानीय सेवा या योग्य सलाहकार से पूछें।",
    ],
    "hinglish": [
        "Wahi step choose karein jo safe lage; aap kabhi bhi ruk sakti hain ya direction badal sakti hain.",
        "Agar safe aur useful ho, toh kya hua aur kab hua privately note kar sakti hain. Help ke liye record banana zaroori nahi.",
        "Apne area ke process aur options ke liye verified local service ya qualified advisor se poochhein.",
    ],
}


def complaint_guidance(language: str, emergency: bool = False) -> dict:
    emergency_guidance = {
        "en": [
            "If you may be in immediate danger, move to a safer place if you can.",
            "Contact an appropriate official emergency service directly, or a trusted person who can stay with you.",
            "SafeHer AI cannot contact responders or dispatch help.",
        ],
        "hi": [
            "यदि तत्काल खतरा हो, तो संभव हो तो सुरक्षित जगह जाएँ।",
            "उचित आधिकारिक आपातकालीन सेवा से सीधे संपर्क करें, या किसी भरोसेमंद व्यक्ति से संपर्क करें जो आपके साथ रह सके।",
            "SafeHer AI सहायता भेज या responders को संपर्क नहीं कर सकता।",
        ],
        "hinglish": [
            "Agar abhi immediate danger ho, toh ho sake toh safe jagah par jaayein.",
            "Appropriate official emergency service ko directly contact karein, ya kisi trusted person ko jo aapke saath reh sake.",
            "SafeHer AI responders ko contact ya dispatch nahi kar sakta.",
        ],
    }
    return {
        "guidance": emergency_guidance[language] if emergency else GUIDANCE[language],
        "emergency": emergency,
        "stored": False,
        "disclaimer": "General safety guidance only; not legal advice or an emergency service." if emergency else "General organization guidance only; not legal advice and not a description of a jurisdiction-specific process.",
    }
