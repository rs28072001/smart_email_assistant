import pytest
from unittest.mock import Mock, patch
from nodes import EmailNodes
from state import EmailState, EmailMessage

class TestEmailNodes:
    def setup_method(self):
        self.nodes = EmailNodes()
    
    def test_classify_intent_node(self):
        mock_state = {
            "email": EmailMessage(
                from_email="test@example.com",
                to="support@company.com", 
                subject="Test",
                body="I have a problem with your service"
            )
        }
        
        with patch.object(self.nodes.llm, 'invoke') as mock_llm:
            mock_llm.return_value = '{"intent": "complaint", "tone": "frustrated", "confidence": 0.9}'
            
            result = self.nodes.classify_intent_node(mock_state)
            
            assert result["intent"] == "complaint"
            assert result["tone"] == "frustrated"
            assert result["confidence"] == 0.9
    
    def test_summarize_node(self):
        mock_state = {
            "email": EmailMessage(
                from_email="test@example.com",
                to="support@company.com",
                subject="Test",
                body="Payment failed multiple times"
            ),
            "intent": "complaint",
            "tone": "frustrated"
        }
        
        with patch.object(self.nodes.llm, 'invoke') as mock_llm:
            mock_llm.return_value = "Customer reports payment failures and is frustrated"
            
            result = self.nodes.summarize_node(mock_state)
            
            assert "payment" in result["summary"].lower()
    
    def test_decision_node_escalate(self):
        mock_state = {
            "intent": "complaint",
            "confidence": 0.7,
            "tone": "angry"
        }
        
        result = self.nodes.decision_node(mock_state)
        assert result["escalate"] is True
    
    def test_decision_node_no_escalate(self):
        mock_state = {
            "intent": "inquiry", 
            "confidence": 0.9,
            "tone": "neutral"
        }
        
        result = self.nodes.decision_node(mock_state)
        assert result["escalate"] is False