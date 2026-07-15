"""
Security Layer
Input sanitization, PII detection/masking, output validation
"""

import re
from typing import Optional
from langsmith import traceable

class InputSanitizer:
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"forget\s+(all\s+)?previous",
        r"new\s+instructions\s*:",
        r"system\s*prompt",
        r"----\s*end\s*(of)?\s*prompt",
        r"pretend\s+you\s+are",
        r"act\s+as\s+(if\s+)?you",
        r"bypass\s+(all\s+)?restrictions",
        r"reveal\s+(your|the)\s+(system|instructions|prompt)",
        r"you\s+are\s+now\s+(DAN|jailbroken)",
    ]

    def __init__(self):
        self.patterns = [
            re.compile(p, re.IGNORECASE)
            for p in self.INJECTION_PATTERNS
        ]

    def check(self, text: str) -> tuple[bool, Optional[str]]:
        """
        Check if input is safe
        """
        is_safe: bool = True
        rejection_reason: str = None
        for pattern in self.patterns:
            if pattern.search(text):
                is_safe = False
                rejection_reason = "Blocked: potential prompt injection detected!"
                break
        return is_safe, rejection_reason

    def clean(self, text: str) -> str:
        """
        Removes potentially dangerous delimiters from input
        """
        text = re.sub(r'[-]{3,}', '', text)
        text = re.sub(r'[=]{3,}', '', text)
        text = text.replace('{{', '{ {').replace('}}', '} }')
        return text.strip()

class PIIDetector:
    PATTERNS = {
        "email": re.compile(
            r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        ),
        "phone": re.compile(
            r'\b\(?\d{3}\)?[-.\s]?\d{3}[-. \s]?\d{4}\b'
        ),
        "ssn": re.compile(
            r'\b\d{3}-\d{2}-\d{4}\b'
        ),
        "credit_card": re.compile(
            r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|6(?:011|5[0-9][0-9])[0-9]{12}|3[47][0-9]{13})\b'
        )
    }

    MASK_MAP = {
        "email": "[EMAIL REDACTED]",
        "phone": "[PHONE REDACTED]",
        "ssn": "[SSN REDACTED]",
        "credit_card": "[CARD REDACTED]"
    }

    def detect(self, text: str) -> dict[str, list[str]]:
        found = {}
        for pii_type, pattern in self.PATTERNS.items():
            matches = pattern.findall(text)
            if matches:
                found[pii_type] = matches
        return found
    
    def mask(self, text: str) -> str:
        masked = text
        for pii_type, pattern in self.PATTERNS.items():
            masked = pattern.sub(self.MASK_MAP[pii_type], masked)
        return masked
    
class OutputValidator:
    HARMFUL_PATTERNS = [
        re.compile(
            r"here('s| is) (how|the way) to (hack|steal|attack)", re.I
        ),
        re.compile(
            r"password\s + is\s", re.I
        ),
        re.compile(
            r"api[_\s]?key\s*[:=]", re.I
        )
    ]

    def __init__(self):
        self.pii_detector = PIIDetector()
    
    def validate(self, output: str) -> tuple[str, list[str]]:
        warnings = []
        pii_found = self.pii_detector.detect(output)
        
        if pii_found:
            output = self.pii_detector.mask(output)
            warnings.append(f"PII masked in output: {list(pii_found.keys())}")
        
        for pattern in self.HARMFUL_PATTERNS:
            if pattern.search(output):
                output = "[Response Blocked: potentially harmful content]"
                warnings.append("Harmful content blocked")
                break

        return output, warnings

class SecurityPipeline:
    """
    Complete security pipeline for input & output wire into API
    """

    def __init__(self):
        self.sanitizer = InputSanitizer()
        self.pii_detector = PIIDetector()
        self.output_validator = OutputValidator()

    @traceable(name= "security_check_input")
    def check_input(self, text: str) -> tuple[bool, str, list[str]]:
        is_allowed: bool = True
        cleaned_text: str = ""
        notes = []

        is_safe, reason = self.sanitizer.check(text)
        if not is_safe:
            is_allowed = False
            notes.append(reason)
            return is_allowed, cleaned_text, notes
        
        cleaned_text = self.sanitizer.clean(text)

        pii_found = self.pii_detector.detect(cleaned_text)
        if pii_found:
            cleaned_text = self.pii_detector.mask(cleaned_text)
            notes.append(f"Input PII masked: {list(pii_found.keys())}")
        
        return is_allowed, cleaned_text, notes
    
    @traceable(name= "security_check_output")
    def check_output(self, text: str) -> tuple[str, list[str]]:
        return self.output_validator.validate(text)