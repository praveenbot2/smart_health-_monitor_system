"""
Gemini AI API Integration - Interactive Health Assistant
Complete ChatGPT-like health assistant using Google's Gemini Free API
Features:
- Multi-turn conversations
- Symptom analysis with severity assessment
- Health risk prediction and scoring
- Comprehensive health report generation
- Evidence-based health guidance
"""

import os
import json
import re
import warnings
from typing import Dict, List, Any, Optional
from datetime import datetime

HAS_GEMINI_NEW = False
HAS_GEMINI_LEGACY = False

try:
    from google import genai as genai_new
    HAS_GEMINI_NEW = True
except ImportError:
    genai_new = None

if not HAS_GEMINI_NEW:
    try:
        # Legacy fallback; silence deprecation warning at import time.
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', FutureWarning)
            import google.generativeai as genai_legacy
        HAS_GEMINI_LEGACY = True
    except ImportError:
        genai_legacy = None


class GeminiHealthAssistant:
    """Professional Health Assistant powered by Gemini Free API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.conversation_history = {}
        self.is_available = False
        self.model = None
        self.client = None
        self.provider = None
        self.model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
        
        if self.api_key:
            try:
                if HAS_GEMINI_NEW:
                    self.client = genai_new.Client(api_key=self.api_key)
                    self.provider = 'google.genai'
                    self.is_available = True
                    print("✓ Gemini Health Assistant initialized (google.genai)")
                elif HAS_GEMINI_LEGACY:
                    genai_legacy.configure(api_key=self.api_key)
                    self.model = genai_legacy.GenerativeModel(
                        self.model_name,
                        system_instruction=self._system_prompt()
                    )
                    self.provider = 'google.generativeai'
                    self.is_available = True
                    print("✓ Gemini Health Assistant initialized (legacy SDK)")
                else:
                    print("⚠ Gemini SDK not installed")
            except Exception as e:
                print(f"✗ Gemini initialization failed: {e}")
                self.model = None
                self.client = None
        else:
            if not HAS_GEMINI_NEW and not HAS_GEMINI_LEGACY:
                print("⚠ Gemini SDK not installed")
            else:
                print("⚠ GEMINI_API_KEY not set")

    def _generate_text(self, prompt: str) -> str:
        """Generate response text using whichever Gemini SDK is available."""
        if self.provider == 'google.genai' and self.client:
            full_prompt = f"{self._system_prompt()}\n\n{prompt}"
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt
            )
            return getattr(response, 'text', None) or "I understand your question. Could you provide a bit more detail so I can help better?"

        if self.provider == 'google.generativeai' and self.model:
            response = self.model.generate_content(prompt)
            return getattr(response, 'text', None) or "I understand your question. Could you provide a bit more detail so I can help better?"

        raise RuntimeError('Gemini provider is not available')
    
    def _system_prompt(self) -> str:
        return """You are an empathetic and knowledgeable health assistant.

CORE RESPONSIBILITIES:
1. Answer health questions with accurate, evidence-based information
2. Analyze patient symptoms compassionately
3. Assess health risk levels clearly
4. Provide actionable health recommendations
5. Always emphasize consulting healthcare professionals

RESPONSE PATTERN:
- Be clear and structured in your analysis
- Use bullet points for recommendations
- Explain severity/risk levels explicitly
- Include when to seek emergency care
- Provide confidence level in your assessment

IMPORTANT REMINDERS:
- You're an informational AI, not a doctor
- Encourage professional medical consultation
- For emergencies, always recommend immediate care
- Be empathetic and supportive
- Ask clarifying questions when needed"""
    
    def chat(self, user_id: str, message: str, context: Optional[Dict] = None) -> Dict:
        """ChatGPT-like multi-turn conversation"""
        if not self.is_available:
            fallback = self._fallback_response(message, context)
            return {
                'success': True,
                'response': fallback,
                'timestamp': datetime.utcnow().isoformat(),
                'mode': 'fallback'
            }
        
        try:
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []
            
            prompt = message
            if context:
                prompt = f"{self._format_context(context)}\n\nQuestion: {message}"
            
            response_text = self._generate_text(prompt)
            
            self.conversation_history[user_id].append({
                'user': message,
                'assistant': response_text,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            if len(self.conversation_history[user_id]) > 50:
                self.conversation_history[user_id] = self.conversation_history[user_id][-50:]
            
            return {
                'success': True,
                'response': response_text,
                'timestamp': datetime.utcnow().isoformat(),
                'mode': 'gemini'
            }
        except Exception as e:
            fallback = self._fallback_response(message, context)
            return {
                'success': True,
                'response': fallback,
                'timestamp': datetime.utcnow().isoformat(),
                'mode': 'fallback',
                'warning': str(e)
            }

    def _fallback_response(self, message: str, context: Optional[Dict] = None) -> str:
        """Provide helpful local fallback responses when Gemini is unavailable."""
        message_clean = (message or '').strip()
        message_low = message_clean.lower()
        context_note = ""
        if context and context.get('vitals'):
            context_note = "\n\nI can also see your latest vitals context and can explain those if you ask."

        if not message_clean:
            return "Please type a question, and I’ll do my best to help." + context_note

        if any(k in message_low for k in ['hello', 'hi', 'hey', 'namaste']):
            return (
                "Hi! 👋 Ask me anything about symptoms, medications, lifestyle, mental wellness, fitness, or general knowledge. "
                "If your question is urgent medical, please contact emergency care immediately."
                + context_note
            )

        if any(k in message_low for k in ['fever', 'temperature']):
            return (
                "For fever, keep hydration high, rest, and monitor temperature every 4-6 hours. "
                "Seek urgent care if temperature is very high, lasts more than 3 days, or includes breathing issues."
                + context_note
            )

        if any(k in message_low for k in ['headache', 'pain', 'cough', 'cold', 'sore throat', 'vomit', 'nausea']):
            return (
                "For these symptoms, track onset, duration, severity, temperature, hydration, and any triggers. "
                "If severe, persistent, or worsening (especially breathing issues/chest pain), seek medical care quickly. "
                "I can help you structure a symptom summary for your doctor if you want."
                + context_note
            )

        if any(k in message_low for k in ['diet', 'food', 'nutrition']):
            return (
                "A balanced approach works best: more vegetables, fruits, whole grains, lean protein, and water; "
                "reduce excess sugar, salt, and ultra-processed foods."
                + context_note
            )

        if any(k in message_low for k in ['exercise', 'workout', 'fitness']):
            return (
                "Start with 30 minutes of moderate activity (like brisk walking) at least 5 days/week, "
                "plus 2 days of light strength work and proper sleep/recovery."
                + context_note
            )

        if any(k in message_low for k in ['stress', 'anxiety', 'depression', 'sleep', 'mental']):
            return (
                "For mental wellness: keep a consistent sleep schedule, reduce caffeine late-day, practice 10 minutes breathing/mindfulness, "
                "and stay socially connected. If symptoms are intense or prolonged, talk to a licensed professional."
                + context_note
            )

        if any(k in message_low for k in ['medicine', 'medication', 'tablet', 'dose', 'drug', 'side effect']):
            return (
                "Medication safety basics: follow prescribed dose/time, avoid self-mixing medicines, check allergy interactions, "
                "and report side effects early. If you share the medicine name, I can provide a general safety checklist."
                + context_note
            )

        if any(k in message_low for k in ['blood pressure', 'bp', 'heart rate', 'oxygen', 'spo2', 'vital', 'vitals']):
            vitals_text = ""
            if context and context.get('vitals'):
                vitals_text = f" Latest vitals I can see: {context.get('vitals')}."
            return (
                "I can explain vitals in plain language: normal ranges, what may be concerning, and what to monitor next."
                + vitals_text
                + " Ask: 'Explain my vitals one by one'."
            )

        if any(k in message_low for k in ['code', 'python', 'javascript', 'java', 'programming', 'bug', 'algorithm', 'math']):
            return (
                "Yes, I can also help with coding and technical questions. "
                "Please share the exact problem, language, and expected output, and I’ll give a step-by-step solution."
            )

        if message_clean.endswith('?') or len(message_clean.split()) > 3:
            return (
                f"Great question: \"{message_clean}\". "
                "I can answer this in detail, but Gemini is currently not connected. "
                "I can still provide a concise practical answer if you want a short, medium, or detailed version."
                + context_note
            )

        return (
            "I can help with health guidance, symptom understanding, lifestyle tips, medication safety questions, and general knowledge. "
            "Tell me your question in one line and I’ll respond specifically. "
            "For emergencies, seek immediate care."
            + context_note
        )
    
    def _format_context(self, ctx: Dict) -> str:
        lines = ["[PATIENT CONTEXT]"]
        if ctx.get('vitals'):
            lines.append("Vital Signs: " + str(ctx['vitals']))
        if ctx.get('symptoms'):
            lines.append("Symptoms: " + ctx['symptoms'])
        if ctx.get('history'):
            lines.append("Medical History: " + ctx['history'])
        return "\n".join(lines)
    
    def analyze_symptoms(self, symptoms: List[str]) -> Dict:
        """Symptom analysis with severity"""
        if not self.is_available:
            return {'success': False, 'analysis': 'Service unavailable'}
        
        prompt = f"""Analyze these symptoms: {', '.join(symptoms)}

Provide:
1. **Severity Level**: Low/Medium/High/Critical
2. **Possible Causes**: Common conditions (educational info only)
3. **Immediate Actions**: What patient should do now
4. **When to See Doctor**: Recommended timeframe
5. **Emergency Signals**: When to seek immediate care
6. **Monitoring**: What to track"""
        
        try:
            response_text = self._generate_text(prompt)
            return {
                'success': True,
                'analysis': response_text,
                'severity': self._parse_severity(response_text),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def assess_health_risk(self, vitals: Dict, patient_info: Dict) -> Dict:
        """Comprehensive health risk assessment"""
        if not self.is_available:
            return {'success': False}
        
        prompt = f"""Assess health risk for patient:

VITAL SIGNS: {json.dumps(vitals)}
PATIENT INFO: {json.dumps(patient_info)}

Analyze and provide:
1. **Risk Level**: Low/Medium/High/Critical  
2. **Risk Score**: 0-100
3. **Primary Risks**: Top health concerns
4. **Contributing Factors**: What increases risk
5. **Recommendations**: Immediate and long-term actions
6. **Monitoring Plan**: Frequency and parameters"""
        
        try:
            response_text = self._generate_text(prompt)
            return {
                'success': True,
                'analysis': response_text,
                'risk_level': self._parse_risk_level(response_text),
                'risk_score': self._parse_risk_score(response_text),
                'recommendations': self._extract_list_items(response_text),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_health_report(self, patient_data: Dict) -> Dict:
        """Generate comprehensive health report"""
        if not self.is_available:
            return {'success': False}
        
        prompt = f"""Generate protective health report for patient data:
        
{json.dumps(patient_data, indent=2)}

Structure as:
1. **Executive Summary**: Overall health status in 2-3 sentences
2. **Vital Signs Analysis**: Interpretation of measurements
3. **Health Metrics**: Key indicators and assessment
4. **Identified Risks**: Health concerns to address
5. **Positive Factors**: Healthy aspects to maintain
6. **Action Plan**: Recommended lifestyle changes and medical follow-up
7. **Monitoring Plan**: What to track and frequency
8. **Conclusion**: Long-term health outlook"""
        
        try:
            response_text = self._generate_text(prompt)
            return {
                'success': True,
                'report': response_text,
                'summary': response_text[:200],
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # Helper methods
    def _parse_severity(self, text: str) -> str:
        text_low = text.lower()
        for level in ['critical', 'high', 'medium', 'low']:
            if level in text_low:
                return level.capitalize()
        return 'Medium'
    
    def _parse_risk_level(self, text: str) -> str:
        text_low = text.lower()
        if 'critical' in text_low:
            return 'Critical'
        elif 'high' in text_low:
            return 'High'
        elif 'medium' in text_low or 'moderate' in text_low:
            return 'Medium'
        elif 'low' in text_low:
            return 'Low'
        return 'Medium'
    
    def _parse_risk_score(self, text: str) -> int:
        matches = re.findall(r'(\d+)\s*(?:/100|%|score)', text.lower())
        if matches:
            return min(100, int(matches[0]))
        return 50
    
    def _extract_list_items(self, text: str) -> List[str]:
        items = []
        for line in text.split('\n'):
            if re.match(r'^[\s]*[-•*]\s+', line):
                item = re.sub(r'^[\s]*[-•*]\s+', '', line).strip()
                if item:
                    items.append(item)
        return items[:10]
    
    def get_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        return self.conversation_history.get(user_id, [])[-limit:]
    
    def clear_history(self, user_id: str) -> bool:
        if user_id in self.conversation_history:
            self.conversation_history[user_id] = []
            return True
        return False


_instance = None

def get_gemini_assistant() -> GeminiHealthAssistant:
    """Singleton getter"""
    global _instance
    if _instance is None:
        _instance = GeminiHealthAssistant()
    return _instance
