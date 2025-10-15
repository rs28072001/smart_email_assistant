import pytest
import json
from main import SmartEmailAssistant

class TestWorkflow:
    def test_complete_workflow(self):
        assistant = SmartEmailAssistant()
        
        test_email = {
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
        
        result = assistant.process_email(test_email)
        
        assert "subject" in result
        assert "body" in result
        assert "to" in result
        assert "from" in result
        assert "intent" in result
        assert "escalate" in result
        assert isinstance(result["escalate"], bool)