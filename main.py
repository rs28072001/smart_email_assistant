#!/usr/bin/env python3
import json
import sys
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from nodes import EmailNodes
from state import EmailState, EmailMessage
import time

class SmartEmailAssistant:
    def __init__(self):
        self.nodes = EmailNodes()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(EmailState)
        
        # Add nodes
        workflow.add_node("classify_intent", self.nodes.classify_intent_node)
        workflow.add_node("summarize", self.nodes.summarize_node)
        workflow.add_node("memory", self.nodes.memory_node)
        workflow.add_node("generate_reply", self.nodes.generate_reply_node)
        workflow.add_node("decision", self.nodes.decision_node)
        
        # Define workflow
        workflow.set_entry_point("classify_intent")
        workflow.add_edge("classify_intent", "summarize")
        workflow.add_edge("summarize", "memory")
        workflow.add_edge("memory", "generate_reply")
        workflow.add_edge("generate_reply", "decision")
        workflow.add_edge("decision", END)
        
        return workflow.compile()
    
    def process_email(self, email_input: Dict[str, Any]) -> Dict[str, Any]:
        """Process an incoming email and generate response"""
        
        # Prepare email message
        email_msg = EmailMessage(
            from_email=email_input["from"],
            to=email_input["to"],
            subject=email_input["subject"],
            body=email_input["body"]
        )
        
        # Initial state
        initial_state = {
            "email": email_msg,
            "history": email_input.get("history", []),
            "intent": "",
            "summary": "",
            "memory_context": "",
            "tone": "",
            "reply_subject": "",
            "reply_body": "",
            "escalate": False,
            "confidence": 0.0,
            "timestamp": ""
        }
        
        # Execute workflow
        result = self.graph.invoke(initial_state)
        
        # Format output
        output = {
            "subject": result["reply_subject"],
            "body": result["reply_body"],
            "to": result["email"].from_email,
            "from": result["email"].to,
            "intent": result["intent"],
            "escalate": result["escalate"],
            "confidence": result["confidence"],
            "summary": result["summary"]
        }
        
        return output

def main():
    """Main function with built-in sample email - no command line arguments needed"""
    
    # Sample email input (same as the assignment example)
    sample_email = {
        "from": "sarah@example.com",
        "to": "support@yourapp.com",
        "subject": "Payment not going through",
        "body": "Hi, I tried paying for my subscription twice but it keeps failing. Can you please fix this?",
        "history": [
            {
                "from": "support@yourapp.com",
                "to": "sarah@example.com",
                "body": "We've updated your billing details last week. Please try again."
            }
        ]
    }
    
    print("🚀 Starting Smart Email Assistant...")
    print("📧 Processing Sample Email:")
    print(json.dumps(sample_email, indent=2))
    print("\n" + "="*50 + "\n")
    
    # Create assistant and process email
    assistant = SmartEmailAssistant()
    result = assistant.process_email(sample_email)
    
    print("✅ Processing Complete!")
    print("📨 Generated Response:")
    print(json.dumps(result, indent=2))

def test_multiple_emails():
    """Optional: Test with multiple email types"""
    print("\n" + "="*60)
    print("🧪 TESTING MULTIPLE EMAIL TYPES")
    print("="*60)
    
    test_emails = [
        {
            "name": "Complaint Email",
            "data": {
                "from": "john@example.com",
                "to": "support@yourapp.com", 
                "subject": "Very disappointed with service",
                "body": "Your service has been terrible lately. I've experienced multiple outages and the support is slow. This is unacceptable for a paying customer!",
                "history": []
            }
        },
        {
            "name": "Inquiry Email", 
            "data": {
                "from": "alice@company.org",
                "to": "support@yourapp.com",
                "subject": "Question about enterprise pricing",
                "body": "Hello, I'm interested in your enterprise plan. Could you please send me information about pricing and features? Also, do you offer any discounts for non-profits?",
                "history": []
            }
        },
        {
            "name": "Feedback Email",
            "data": {
                "from": "mike@user.com", 
                "to": "support@yourapp.com",
                "subject": "Loving the new update!",
                "body": "Just wanted to say the latest app update is fantastic! The new dashboard is much more intuitive and the performance improvements are noticeable. Great work team!",
                "history": []
            }
        }
    ]
    
    assistant = SmartEmailAssistant()
    
    for test in test_emails:
        print(f"\n📝 Testing: {test['name']}")
        print("-" * 40)
        
        result = assistant.process_email(test["data"])
        
        print(f"📧 Input Subject: {test['data']['subject']}")
        print(f"🎯 Detected Intent: {result['intent']}")
        print(f"🚨 Escalate: {result['escalate']}")
        print(f"💬 Summary: {result['summary']}")
        print(f"📨 Reply Subject: {result['subject']}")
        print(f"📄 Reply Preview: {result['body'][:100]}...")
        print()

if __name__ == "__main__":
    # Run the main sample email
    # main()
    
    # Uncomment the line below to test multiple email types
    test_multiple_emails()