from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage
from pydantic import BaseModel, field_validator
from typing import Optional
import os

# Pydantic Model for AI Analysis Result
class EmailAnalysis(BaseModel):
    language: str
    sentiment: str
    confidence: float
    escalate: bool
    summary: str

    @field_validator('language', 'sentiment', 'summary')
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

# LLM Analysis Class
class LLMEmailAnalyzer:
    def __init__(self, openai_api_key: str = None, model: str = "gpt-4"):
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("Please set your OpenAI API key or pass it as a parameter.")
        self.llm = ChatOpenAI(openai_api_key=self.api_key, model_name=model, temperature=0)

        self.prompt_template = ChatPromptTemplate.from_template(
            """You are an email analysis assistant.
Given the email text, analyze it and return in JSON format:

1. language: detect the language (Hindi, English, Hinglish, Punjabi, etc.)
2. sentiment: classify the email into one of: complaint, request, feedback, inquiry, neutral, conversational, greetings
3. confidence: a float number (0 to 1) indicating confidence in your classification
4. escalate: true if this email requires human intervention, false if AI can reply
5. summary: summarize what the email is saying and its tone in 1-2 sentences

Return ONLY valid JSON with these keys.

Email:
{text}"""
        )

    def analyze(self, email_text: str) -> EmailAnalysis:
        prompt = self.prompt_template.format_prompt(text=email_text).to_messages()
        response = self.llm(prompt)
        # LangChain returns a list of messages, pick content from last message
        content = response.content if hasattr(response, 'content') else response[-1].content

        import json
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # fallback if LLM returns something slightly off
            # try extracting JSON inside text
            import re
            match = re.search(r'{.*}', content, re.DOTALL)
            if match:
                data = json.loads(match.group())
            else:
                data = {
                    "language": "Unknown",
                    "sentiment": "neutral",
                    "confidence": 0.0,
                    "escalate": False,
                    "summary": content[:200]
                }

        # Validate with Pydantic
        return EmailAnalysis(**data)