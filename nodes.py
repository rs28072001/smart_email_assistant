from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Dict, Any
import json
from datetime import datetime

from config import get_llm
from memory_manager import MemoryManager
from state import EmailState

class EmailNodes:
    def __init__(self):
        self.llm = get_llm()
        self.memory_manager = MemoryManager()
    
    def classify_intent_node(self, state: EmailState) -> Dict[str, Any]:
        """Classify email intent using LLM"""
        prompt = ChatPromptTemplate.from_template("""
        Classify the intent of this email as one of: complaint, request, feedback, inquiry.
        Also analyze the tone of the email and provide a confidence score between 0 and 1.
        
        Email: {email_body}
        
        Respond in JSON format:
        {{
            "intent": "complaint|request|feedback|inquiry",
            "tone": "angry|frustrated|neutral|happy|urgent",
            "confidence": 0.95
        }}
        """)
        
        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({"email_body": state["email"].body})
        
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            result = {
                "intent": "inquiry",
                "tone": "neutral", 
                "confidence": 0.5
            }
        
        # Save to memory
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
        
        return {
            "intent": result["intent"],
            "tone": result["tone"],
            "confidence": result["confidence"],
            "timestamp": datetime.now().isoformat()
        }
    
    def summarize_node(self, state: EmailState) -> Dict[str, Any]:
        """Summarize email content"""
        prompt = ChatPromptTemplate.from_template("""
        Summarize the email briefly in 2-3 lines, focusing on:
        1. The sender's main point or request
        2. The emotional tone and urgency
        3. Key details that need attention
        
        Email: {email_body}
        Tone: {tone}
        Intent: {intent}
        
        Provide only the summary text, no additional commentary.
        """)
        
        chain = prompt | self.llm | StrOutputParser()
        summary = chain.invoke({
            "email_body": state["email"].body,
            "tone": state["tone"],
            "intent": state["intent"]
        })
        
        return {"summary": summary.strip()}
    
    def memory_node(self, state: EmailState) -> Dict[str, Any]:
        """Retrieve and format conversation history"""
        memory_context = self.memory_manager.get_memory_context(state["email"].from_email)
        
        return {"memory_context": memory_context}
    
    def generate_reply_node(self, state: EmailState) -> Dict[str, Any]:
        """Generate appropriate email reply based on intent and context"""
        
        tone_mapping = {
            "complaint": "empathetic and solution-oriented",
            "request": "helpful and efficient", 
            "feedback": "appreciative and engaging",
            "inquiry": "informative and clear"
        }
        
        prompt = ChatPromptTemplate.from_template("""
        You are a professional support agent. Write a polite and context-aware reply to this customer email.
        
        INTENT: {intent}
        TONE TO USE: {required_tone}
        EMAIL SUMMARY: {summary}
        CUSTOMER'S TONE: {customer_tone}
        CONVERSATION HISTORY: {memory_context}
        
        Original Email Subject: {subject}
        
        Guidelines:
        - Match the {required_tone} tone
        - Address the customer by name if possible (extract from email)
        - Be specific and helpful
        - Include relevant details from conversation history
        - Keep it professional but warm
        
        Respond in JSON format:
        {{
            "subject": "Re: Original Subject",
            "body": "Your polite reply here...",
            "tone_used": "description of tone used"
        }}
        """)
        
        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({
            "intent": state["intent"],
            "required_tone": tone_mapping.get(state["intent"], "professional"),
            "summary": state["summary"],
            "customer_tone": state["tone"],
            "memory_context": state["memory_context"],
            "subject": state["email"].subject
        })
        
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            # Fallback reply
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