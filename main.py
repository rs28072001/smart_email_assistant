#!/usr/bin/env python3
import json
import sys
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from nodes import EmailNodes
from state import EmailState, EmailMessage

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
    """Main function to process email from command line input"""
    if len(sys.argv) > 1:
        # Read from file
        with open(sys.argv[1], 'r') as f:
            email_input = json.load(f)
    else:
        # Read from stdin
        input_str = sys.stdin.read()
        email_input = json.loads(input_str)
    
    assistant = SmartEmailAssistant()
    result = assistant.process_email(email_input)
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()