"""Risk detection and analysis for legal documents"""

import logging
import re
from typing import List, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskDetector:
    """Detect risks in legal documents using pattern matching and heuristics"""
    
    # Risk patterns: (pattern, risk_level, description)
    RISK_PATTERNS = [
        # Unlimited liability patterns
        (r"unlimited\s+liability|liability\s+without\s+limit", 
         RiskLevel.CRITICAL, 
         "Unlimited liability clause detected"),
        
        # Indemnification patterns
        (r"indemnif[y|ication]+.*without.*limit|hold\s+harmless\s+against\s+all\s+claims",
         RiskLevel.HIGH,
         "Broad indemnification without limits"),
        
        # Termination clauses
        (r"terminate[d]?\s+without\s+cause|terminate\s+at\s+will|termination\s+without\s+notice",
         RiskLevel.HIGH,
         "Termination without cause or notice provision"),
        
        # Exclusion of liability
        (r"exclude[d]?\s+from\s+liability|not\s+responsible\s+for|disclaim.*liability",
         RiskLevel.MEDIUM,
         "Liability exclusion or disclaimer clause"),
        
        # Payment terms
        (r"payment\s+within\s+\d+\s+days|net\s+\d+|payment\s+terms",
         RiskLevel.LOW,
         "Payment terms specified"),
        
        # Confidentiality breach
        (r"breach.*confidential|disclose.*confidential\s+information",
         RiskLevel.HIGH,
         "Confidentiality breach consequences"),
        
        # Non-compete
        (r"non-?compete|non-?solicitation|restriction\s+on\s+competition",
         RiskLevel.MEDIUM,
         "Non-compete or non-solicitation clause"),
        
        # Jurisdiction/Dispute
        (r"governing\s+law|jurisdiction|dispute\s+resolution|arbitration",
         RiskLevel.MEDIUM,
         "Dispute resolution mechanism specified"),
        
        # Force majeure
        (r"force\s+majeure|act\s+of\s+god|unforeseen\s+circumstances",
         RiskLevel.LOW,
         "Force majeure clause present"),
        
        # Warranty exclusion
        (r"warranty.*excluded|as-?is|without.*warranty|no\s+warranty",
         RiskLevel.MEDIUM,
         "Warranty exclusion or limitation"),
    ]
    
    def __init__(self):
        """Initialize detector"""
        logger.info("Risk detector initialized")
    
    def detect_risks(self, text: str) -> List[Dict]:
        """
        Detect risks in legal text
        
        Args:
            text: Legal document text
        
        Returns:
            List of risk objects with details
        """
        risks = []
        text_lower = text.lower()
        
        for pattern, level, description in self.RISK_PATTERNS:
            matches = list(re.finditer(pattern, text_lower, re.IGNORECASE))
            
            if matches:
                for match in matches:
                    # Extract clause text (100 chars around match)
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    clause_text = text[start:end].strip()
                    
                    # Calculate risk score based on level
                    risk_score = {
                        RiskLevel.LOW: 25,
                        RiskLevel.MEDIUM: 50,
                        RiskLevel.HIGH: 75,
                        RiskLevel.CRITICAL: 100,
                    }[level]
                    
                    risks.append({
                        "risk_level": level,
                        "risk_score": risk_score,
                        "description": description,
                        "clause_text": clause_text,
                        "recommendation": self._get_recommendation(level, description),
                    })
        
        logger.info(f"Detected {len(risks)} risks")
        return risks
    
    @staticmethod
    def _get_recommendation(level: RiskLevel, description: str) -> str:
        """Get mitigation recommendation based on risk"""
        recommendations = {
            RiskLevel.CRITICAL: "⚠️ URGENT: Have legal counsel review immediately",
            RiskLevel.HIGH: "⚠️ HIGH PRIORITY: Negotiate modifications with counterparty",
            RiskLevel.MEDIUM: "Consider requesting clarification or modifications",
            RiskLevel.LOW: "Monitor but generally acceptable",
        }
        return recommendations.get(level, "Review with legal counsel")


# Global instance
_detector: RiskDetector = None


def get_risk_detector() -> RiskDetector:
    """Get or create risk detector instance"""
    global _detector
    if _detector is None:
        _detector = RiskDetector()
    return _detector
