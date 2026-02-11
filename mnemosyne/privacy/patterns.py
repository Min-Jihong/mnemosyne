"""Comprehensive regex patterns for PII detection.

This module provides regex patterns for detecting various types of
personally identifiable information (PII) in text data.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Pattern


class PIICategory(str, Enum):
    """Categories of PII data."""
    FINANCIAL = "financial"
    PERSONAL = "personal"
    CREDENTIALS = "credentials"
    CONTACT = "contact"
    IDENTIFIER = "identifier"


class PIIType(str, Enum):
    """Types of PII that can be detected."""
    # Contact
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    
    # Financial
    CREDIT_CARD = "credit_card"
    BANK_ACCOUNT = "bank_account"
    ROUTING_NUMBER = "routing_number"
    
    # Personal identifiers
    SSN = "ssn"
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    
    # Credentials
    API_KEY = "api_key"
    PASSWORD = "password"
    SECRET_KEY = "secret_key"
    ACCESS_TOKEN = "access_token"
    PRIVATE_KEY = "private_key"
    
    # Personal
    NAME = "name"
    DATE_OF_BIRTH = "date_of_birth"
    IP_ADDRESS = "ip_address"
    MAC_ADDRESS = "mac_address"


@dataclass
class PIIPattern:
    """A pattern for detecting a specific type of PII."""
    pii_type: PIIType
    category: PIICategory
    pattern: Pattern[str]
    replacement: str
    description: str
    confidence: float = 0.9  # How confident we are in matches
    enabled: bool = True


@dataclass
class AllowListEntry:
    """An entry in the allow list that should not be scrubbed."""
    pattern: str
    pii_type: PIIType | None = None  # None means applies to all types
    reason: str = ""


@dataclass
class PatternConfig:
    """Configuration for PII pattern matching."""
    allow_list: list[AllowListEntry] = field(default_factory=list)
    custom_patterns: list[PIIPattern] = field(default_factory=list)
    disabled_types: set[PIIType] = field(default_factory=set)


# Email patterns
EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    re.IGNORECASE
)

# Phone number patterns (US and international)
PHONE_PATTERNS = [
    # US formats: (123) 456-7890, 123-456-7890, 123.456.7890, 1234567890
    re.compile(r'\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
    # International: +1-123-456-7890, +44 20 7123 4567
    re.compile(r'\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b'),
]

# SSN pattern: XXX-XX-XXXX or XXXXXXXXX
SSN_PATTERN = re.compile(
    r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'
)

# Credit card patterns
CREDIT_CARD_PATTERNS = [
    # Visa: 4XXX XXXX XXXX XXXX
    re.compile(r'\b4\d{3}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
    # Mastercard: 5XXX XXXX XXXX XXXX
    re.compile(r'\b5[1-5]\d{2}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
    # Amex: 3XXX XXXXXX XXXXX
    re.compile(r'\b3[47]\d{2}[-\s]?\d{6}[-\s]?\d{5}\b'),
    # Discover: 6011 XXXX XXXX XXXX
    re.compile(r'\b6(?:011|5\d{2})[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
    # Generic 16-digit card number
    re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
]

# Bank account and routing numbers
BANK_ACCOUNT_PATTERN = re.compile(
    r'\b\d{8,17}\b'  # Bank accounts are typically 8-17 digits
)
ROUTING_NUMBER_PATTERN = re.compile(
    r'\b\d{9}\b'  # US routing numbers are exactly 9 digits
)

# API key patterns (common formats)
API_KEY_PATTERNS = [
    # OpenAI: sk-...
    re.compile(r'\bsk-[A-Za-z0-9]{20,}\b'),
    # Anthropic: sk-ant-...
    re.compile(r'\bsk-ant-[A-Za-z0-9-]{20,}\b'),
    # Generic API keys with common prefixes
    re.compile(r'\b(?:api[_-]?key|apikey|api_secret)[=:\s]+["\']?([A-Za-z0-9_-]{16,})["\']?', re.IGNORECASE),
    # AWS access keys: AKIA...
    re.compile(r'\bAKIA[A-Z0-9]{16}\b'),
    # AWS secret keys (40 chars)
    re.compile(r'\b[A-Za-z0-9/+=]{40}\b'),
    # GitHub tokens: ghp_, gho_, ghu_, ghs_, ghr_
    re.compile(r'\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b'),
    # Stripe keys: sk_live_, sk_test_, pk_live_, pk_test_
    re.compile(r'\b(?:sk|pk)_(?:live|test)_[A-Za-z0-9]{24,}\b'),
    # Generic hex tokens (32+ chars)
    re.compile(r'\b[a-f0-9]{32,}\b', re.IGNORECASE),
]

# Password patterns (in config files, URLs, etc.)
PASSWORD_PATTERNS = [
    # password=..., passwd=..., pwd=...
    re.compile(r'(?:password|passwd|pwd)[=:\s]+["\']?([^\s"\']{4,})["\']?', re.IGNORECASE),
    # In URLs: user:password@host
    re.compile(r'://[^:]+:([^@]+)@'),
    # secret=..., token=...
    re.compile(r'(?:secret|token)[=:\s]+["\']?([^\s"\']{8,})["\']?', re.IGNORECASE),
]

# Private key patterns
PRIVATE_KEY_PATTERNS = [
    # PEM format private keys
    re.compile(r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----'),
    # SSH private key content (base64)
    re.compile(r'-----BEGIN OPENSSH PRIVATE KEY-----[\s\S]*?-----END OPENSSH PRIVATE KEY-----'),
]

# IP address patterns
IP_ADDRESS_PATTERNS = [
    # IPv4
    re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'),
    # IPv6 (simplified)
    re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'),
]

# MAC address pattern
MAC_ADDRESS_PATTERN = re.compile(
    r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b'
)

# Date of birth patterns
DOB_PATTERNS = [
    # MM/DD/YYYY, MM-DD-YYYY
    re.compile(r'\b(?:0[1-9]|1[0-2])[/-](?:0[1-9]|[12]\d|3[01])[/-](?:19|20)\d{2}\b'),
    # YYYY-MM-DD (ISO format)
    re.compile(r'\b(?:19|20)\d{2}[-/](?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])\b'),
]

# Address patterns (simplified - full NER would be better)
ADDRESS_PATTERNS = [
    # US street addresses: 123 Main St, 456 Oak Avenue
    re.compile(r'\b\d{1,5}\s+(?:[A-Z][a-z]+\s+){1,3}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Place|Pl|Circle|Cir)\b', re.IGNORECASE),
    # PO Box
    re.compile(r'\bP\.?O\.?\s*Box\s+\d+\b', re.IGNORECASE),
    # ZIP codes (US)
    re.compile(r'\b\d{5}(?:-\d{4})?\b'),
]

# Passport patterns (simplified)
PASSPORT_PATTERN = re.compile(
    r'\b[A-Z]{1,2}\d{6,9}\b'  # Common passport number format
)

# Driver's license patterns (varies by state, simplified)
DRIVERS_LICENSE_PATTERN = re.compile(
    r'\b[A-Z]\d{7,8}\b'  # Common format: letter + 7-8 digits
)


def get_default_patterns() -> list[PIIPattern]:
    """Get the default set of PII detection patterns."""
    patterns = []
    
    # Email
    patterns.append(PIIPattern(
        pii_type=PIIType.EMAIL,
        category=PIICategory.CONTACT,
        pattern=EMAIL_PATTERN,
        replacement="[EMAIL_REDACTED]",
        description="Email addresses",
        confidence=0.95,
    ))
    
    # Phone numbers
    for i, pattern in enumerate(PHONE_PATTERNS):
        patterns.append(PIIPattern(
            pii_type=PIIType.PHONE,
            category=PIICategory.CONTACT,
            pattern=pattern,
            replacement="[PHONE_REDACTED]",
            description=f"Phone numbers (pattern {i+1})",
            confidence=0.85,
        ))
    
    # SSN
    patterns.append(PIIPattern(
        pii_type=PIIType.SSN,
        category=PIICategory.IDENTIFIER,
        pattern=SSN_PATTERN,
        replacement="[SSN_REDACTED]",
        description="Social Security Numbers",
        confidence=0.90,
    ))
    
    # Credit cards
    for i, pattern in enumerate(CREDIT_CARD_PATTERNS):
        patterns.append(PIIPattern(
            pii_type=PIIType.CREDIT_CARD,
            category=PIICategory.FINANCIAL,
            pattern=pattern,
            replacement="[CREDIT_CARD_REDACTED]",
            description=f"Credit card numbers (pattern {i+1})",
            confidence=0.90,
        ))
    
    # API keys
    for i, pattern in enumerate(API_KEY_PATTERNS):
        patterns.append(PIIPattern(
            pii_type=PIIType.API_KEY,
            category=PIICategory.CREDENTIALS,
            pattern=pattern,
            replacement="[API_KEY_REDACTED]",
            description=f"API keys (pattern {i+1})",
            confidence=0.85,
        ))
    
    # Passwords
    for i, pattern in enumerate(PASSWORD_PATTERNS):
        patterns.append(PIIPattern(
            pii_type=PIIType.PASSWORD,
            category=PIICategory.CREDENTIALS,
            pattern=pattern,
            replacement="[PASSWORD_REDACTED]",
            description=f"Passwords (pattern {i+1})",
            confidence=0.80,
        ))
    
    # Private keys
    for i, pattern in enumerate(PRIVATE_KEY_PATTERNS):
        patterns.append(PIIPattern(
            pii_type=PIIType.PRIVATE_KEY,
            category=PIICategory.CREDENTIALS,
            pattern=pattern,
            replacement="[PRIVATE_KEY_REDACTED]",
            description=f"Private keys (pattern {i+1})",
            confidence=0.95,
        ))
    
    # IP addresses
    for i, pattern in enumerate(IP_ADDRESS_PATTERNS):
        patterns.append(PIIPattern(
            pii_type=PIIType.IP_ADDRESS,
            category=PIICategory.IDENTIFIER,
            pattern=pattern,
            replacement="[IP_REDACTED]",
            description=f"IP addresses (pattern {i+1})",
            confidence=0.90,
        ))
    
    # MAC addresses
    patterns.append(PIIPattern(
        pii_type=PIIType.MAC_ADDRESS,
        category=PIICategory.IDENTIFIER,
        pattern=MAC_ADDRESS_PATTERN,
        replacement="[MAC_REDACTED]",
        description="MAC addresses",
        confidence=0.90,
    ))
    
    # Date of birth
    for i, pattern in enumerate(DOB_PATTERNS):
        patterns.append(PIIPattern(
            pii_type=PIIType.DATE_OF_BIRTH,
            category=PIICategory.PERSONAL,
            pattern=pattern,
            replacement="[DOB_REDACTED]",
            description=f"Dates of birth (pattern {i+1})",
            confidence=0.70,  # Lower confidence - could be any date
        ))
    
    # Addresses
    for i, pattern in enumerate(ADDRESS_PATTERNS):
        patterns.append(PIIPattern(
            pii_type=PIIType.ADDRESS,
            category=PIICategory.CONTACT,
            pattern=pattern,
            replacement="[ADDRESS_REDACTED]",
            description=f"Physical addresses (pattern {i+1})",
            confidence=0.75,
        ))
    
    # Passport
    patterns.append(PIIPattern(
        pii_type=PIIType.PASSPORT,
        category=PIICategory.IDENTIFIER,
        pattern=PASSPORT_PATTERN,
        replacement="[PASSPORT_REDACTED]",
        description="Passport numbers",
        confidence=0.70,
    ))
    
    # Driver's license
    patterns.append(PIIPattern(
        pii_type=PIIType.DRIVERS_LICENSE,
        category=PIICategory.IDENTIFIER,
        pattern=DRIVERS_LICENSE_PATTERN,
        replacement="[LICENSE_REDACTED]",
        description="Driver's license numbers",
        confidence=0.65,
    ))
    
    return patterns


def get_patterns_by_level(level: str) -> list[PIIPattern]:
    """
    Get patterns filtered by scrubbing level.
    
    Args:
        level: One of 'minimal', 'standard', 'aggressive'
        
    Returns:
        List of patterns appropriate for the level
    """
    all_patterns = get_default_patterns()
    
    if level == "aggressive":
        # All patterns enabled
        return all_patterns
    
    elif level == "standard":
        # Exclude low-confidence patterns
        return [p for p in all_patterns if p.confidence >= 0.75]
    
    elif level == "minimal":
        # Only high-confidence, high-risk patterns
        high_risk_types = {
            PIIType.SSN,
            PIIType.CREDIT_CARD,
            PIIType.API_KEY,
            PIIType.PASSWORD,
            PIIType.PRIVATE_KEY,
        }
        return [
            p for p in all_patterns 
            if p.pii_type in high_risk_types and p.confidence >= 0.80
        ]
    
    return all_patterns


def get_patterns_by_category(category: PIICategory) -> list[PIIPattern]:
    """Get all patterns for a specific category."""
    return [p for p in get_default_patterns() if p.category == category]


def get_patterns_by_type(pii_type: PIIType) -> list[PIIPattern]:
    """Get all patterns for a specific PII type."""
    return [p for p in get_default_patterns() if p.pii_type == pii_type]


class PatternMatcher:
    """Utility class for matching PII patterns in text."""
    
    def __init__(
        self,
        patterns: list[PIIPattern] | None = None,
        config: PatternConfig | None = None,
    ):
        """
        Initialize the pattern matcher.
        
        Args:
            patterns: List of patterns to use (defaults to all patterns)
            config: Configuration for pattern matching
        """
        self.patterns = patterns or get_default_patterns()
        self.config = config or PatternConfig()
        
        # Apply config
        if self.config.disabled_types:
            self.patterns = [
                p for p in self.patterns 
                if p.pii_type not in self.config.disabled_types
            ]
        
        # Add custom patterns
        self.patterns.extend(self.config.custom_patterns)
        
        # Compile allow list patterns
        self._allow_patterns: list[tuple[re.Pattern[str], PIIType | None]] = []
        for entry in self.config.allow_list:
            try:
                compiled = re.compile(entry.pattern)
                self._allow_patterns.append((compiled, entry.pii_type))
            except re.error:
                pass  # Skip invalid patterns
    
    def is_allowed(self, text: str, pii_type: PIIType) -> bool:
        """Check if a matched text is in the allow list."""
        for pattern, allowed_type in self._allow_patterns:
            if allowed_type is not None and allowed_type != pii_type:
                continue
            if pattern.search(text):
                return True
        return False
    
    def find_matches(self, text: str) -> list[tuple[PIIPattern, re.Match[str]]]:
        """
        Find all PII matches in text.
        
        Args:
            text: Text to search
            
        Returns:
            List of (pattern, match) tuples
        """
        matches = []
        
        for pattern in self.patterns:
            if not pattern.enabled:
                continue
            
            for match in pattern.pattern.finditer(text):
                matched_text = match.group(0)
                if not self.is_allowed(matched_text, pattern.pii_type):
                    matches.append((pattern, match))
        
        return matches
    
    def scrub(self, text: str) -> tuple[str, list[tuple[PIIType, str]]]:
        """
        Scrub PII from text.
        
        Args:
            text: Text to scrub
            
        Returns:
            Tuple of (scrubbed_text, list of (pii_type, original_value))
        """
        matches = self.find_matches(text)
        
        matches.sort(key=lambda x: (x[1].start(), -x[1].end()))
        
        deduplicated: list[tuple[PIIPattern, re.Match[str]]] = []
        last_end = -1
        for pattern, match in matches:
            if match.start() >= last_end:
                deduplicated.append((pattern, match))
                last_end = match.end()
        
        deduplicated.sort(key=lambda x: x[1].start(), reverse=True)
        
        scrubbed = text
        found_pii: list[tuple[PIIType, str]] = []
        
        for pattern, match in deduplicated:
            original = match.group(0)
            found_pii.append((pattern.pii_type, original))
            scrubbed = scrubbed[:match.start()] + pattern.replacement + scrubbed[match.end():]
        
        found_pii.reverse()
        
        return scrubbed, found_pii
