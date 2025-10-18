from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Dict, Any
import json
from datetime import datetime
import re

from config import get_llm
from memory_manager import MemoryManager
from state import EmailState

class EmailNodes:
    def __init__(self):
        try:
            self.llm = get_llm()
            self.memory_manager = MemoryManager()
        except Exception as e:
            print(f"Warning: LLM initialization failed: {e}")
            self.llm = None
    
    def safe_llm_call(self, prompt_template, variables):
        """Safe LLM call with fallback"""
        if self.llm is None:
            return self.get_fallback_response(prompt_template, variables)
        
        try:
            prompt = ChatPromptTemplate.from_template(prompt_template)
            chain = prompt | self.llm | StrOutputParser()
            response = chain.invoke(variables)
            return response
        except Exception as e:
            print(f"LLM Error: {e}")
            return self.get_fallback_response(prompt_template, variables)
    
    def get_fallback_response(self, prompt_template, variables):
        """Provide intelligent fallback responses"""
        email_body = variables.get('email_body', '').lower()
        
        # Intent classification fallback
        if "classify the intent" in prompt_template:
            if any(word in email_body for word in ['problem', 'issue', 'not working', 'failed']):
                return '{"intent": "complaint", "tone": "frustrated", "confidence": 0.9}'
            elif any(word in email_body for word in ['please', 'can you', 'help']):
                return '{"intent": "request", "tone": "neutral", "confidence": 0.85}'
            else:
                return '{"intent": "inquiry", "tone": "neutral", "confidence": 0.8}'
        
        # Summary fallback
        elif "summarize the email" in prompt_template:
            return f"Customer reports: {email_body[:100]}..."
        
        # Reply generation fallback
        elif "Write a polite and context-aware reply" in prompt_template:
            intent = variables.get('intent', 'inquiry')
            if intent == "complaint":
                return '''{
    "subject": "Re: Your Issue",
    "body": "I understand you're experiencing an issue and I apologize for the inconvenience. Let me help resolve this for you.",
    "tone_used": "empathetic"
}'''
            else:
                return '''{
    "subject": "Re: Your Request", 
    "body": "Thank you for your message. I'll be happy to assist you with this.",
    "tone_used": "helpful"
}'''
        
        return "Fallback response"
    
    def classify_intent_node(self, state: EmailState) -> Dict[str, Any]:
        """Classify email intent using LLM with better error handling"""
        prompt = """
        Classify the intent of this email as one of: complaint, request, feedback, inquiry.
        Also analyze the tone of the email and provide a confidence score between 0 and 1.
        
        Email: {email_body}
        
        Respond in JSON format with exactly this structure:
        {{
            "intent": "complaint|request|feedback|inquiry",
            "tone": "angry|frustrated|neutral|happy|urgent",
            "confidence": 0.95
        }}
        """
        
        response = self.safe_llm_call(prompt, {"email_body": state["email"].body})
        
        # Parse JSON response
        try:
            # Extract JSON from response if it contains other text
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response)
        except (json.JSONDecodeError, AttributeError):
            print("JSON parsing failed, using fallback")
            result = {
                "intent": "request",
                "tone": "neutral", 
                "confidence": 0.9
            }
        
        # Save to memory
        try:
            self.memory_manager.save_memory(
                state["email"].from_email,
                {
                    "from": state["email"].from_email,
                    "to": state["email"].to,
                    "subject": state["email"].subject,
                    "body": state["email"].body,
                    "timestamp": datetime.now().isoformat(),
                    "intent": result["intent"]
                }
            )
        except Exception as e:
            print(f"Memory save error: {e}")
        
        return {
            "intent": result["intent"],
            "tone": result["tone"],
            "confidence": result["confidence"],
            "timestamp": datetime.now().isoformat()
        }
    
    def summarize_node(self, state: EmailState) -> Dict[str, Any]:
        """Summarize email content"""
        prompt = """
        Summarize the email briefly in 2-3 lines, focusing on:
        1. The sender's main point or request
        2. The emotional tone and urgency
        3. Key details that need attention
        
        Email: {email_body}
        Tone: {tone}
        Intent: {intent}
        
        Provide only the summary text, no additional commentary.
        """
        
        summary = self.safe_llm_call(prompt, {
            "email_body": state["email"].body,
            "tone": state["tone"],
            "intent": state["intent"]
        })
        
        return {"summary": summary.strip()}
    
    def memory_node(self, state: EmailState) -> Dict[str, Any]:
        """Retrieve and format conversation history"""
        try:
            memory_context = self.memory_manager.get_memory_context(state["email"].from_email)
        except Exception as e:
            print(f"Memory error: {e}")
            memory_context = "No previous conversation history available."
        
        return {"memory_context": memory_context}
    
    def generate_reply_node(self, state: EmailState) -> Dict[str, Any]:
        """Generate appropriate email reply based on intent and context"""
        
        tone_mapping = {
            "complaint": "empathetic and solution-oriented",
            "request": "helpful and efficient", 
            "feedback": "appreciative and engaging",
            "inquiry": "informative and clear"
        }
        
        prompt = """
        You are a professional support agent. Write a polite and context-aware reply to this customer email.
        
        INTENT: {intent}
        TONE TO USE: {required_tone}
        EMAIL SUMMARY: {summary}
        CUSTOMER'S TONE: {customer_tone}
        CONVERSATION HISTORY: {memory_context}
        
        Original Email Subject: {subject}
        Customer's Email: {email_body}
        
        Guidelines:
        - Match the {required_tone} tone
        - Address the customer by name if possible (extract from email)
        - Be specific and helpful
        - Include relevant details from conversation history
        - Keep it professional but warm
        - For payment issues, suggest checking payment details
        
        Respond in JSON format with exactly this structure:
        {{
            "subject": "Re: Original Subject",
            "body": "Your polite reply here...",
            "tone_used": "description of tone used"
        }}
        """
        
        response = self.safe_llm_call(prompt, {
            "intent": state["intent"],
            "required_tone": tone_mapping.get(state["intent"], "professional"),
            "summary": state["summary"],
            "customer_tone": state["tone"],
            "memory_context": state["memory_context"],
            "subject": state["email"].subject,
            "email_body": state["email"].body
        })
        
        # Parse JSON response
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response)
                
            # Ensure subject starts with "Re: "
            if not result["subject"].startswith("Re: "):
                result["subject"] = f"Re: {result['subject']}"
                
        except (json.JSONDecodeError, AttributeError):
            print("Reply JSON parsing failed, using fallback")
            result = {
                "subject": f"Re: {state['email'].subject}",
                "body": "Thank you for your email. We have received your message and will get back to you shortly.",
                "tone_used": "professional"
            }
        
        return {
            "reply_subject": result["subject"],
            "reply_body": result["body"]
        }
    
    def decision_node(self, state: EmailState) -> Dict[str, Any]:
        """Decide whether to escalate the issue"""
        escalate = False
        
        # Escalation rules
        if state["intent"] == "complaint" and state["confidence"] < 0.8:
            escalate = True
        elif "urgent" in state["tone"].lower() or "angry" in state["tone"].lower():
            if state["confidence"] < 0.7:
                escalate = True
        
        return {"escalate": escalate}