"""
Vertical Domain Templates for methodology-v2

Provides pre-built templates for customer service, legal, and healthcare AI agents.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Customer service intent types"""
    REFUND = "refund"
    INQUIRY = "inquiry"
    COMPLAINT = "complaint"
    TECH_SUPPORT = "tech_support"
    ORDER_STATUS = "order_status"
    RETURN = "return"
    OTHER = "other"


class Sentiment(Enum):
    """Sentiment levels"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


@dataclass
class CustomerQuery:
    """Customer query structure"""
    text: str
    intent: IntentType = IntentType.OTHER
    sentiment: Sentiment = Sentiment.NEUTRAL
    entities: Dict = None
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = {}


class IntentClassifier:
    """Classify customer intent from query text"""
    
    # Intent keywords mapping
    INTENT_PATTERNS = {
        IntentType.REFUND: ["退款", "退錢", "退費", "refund", "money back"],
        IntentType.INQUIRY: ["詢問", "請問", "查詢", "問一下", "inquiry", "question"],
        IntentType.COMPLAINT: ["投訴", "抱怨", "不滿", "太差", "complaint", "unhappy"],
        IntentType.TECH_SUPPORT: ["壞了", "故障", "不能", "問題", "無法", "error", "bug"],
        IntentType.ORDER_STATUS: ["訂單", "物流", " shipment", "delivery", "到了嗎"],
        IntentType.RETURN: ["退貨", "退還", "退货", "return"],
    }
    
    def classify(self, text: str) -> IntentType:
        """Classify intent from text"""
        text_lower = text.lower()
        
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    logger.info(f"Classified intent: {intent.value}")
                    return intent
        
        return IntentType.OTHER


class SentimentAnalyzer:
    """Analyze sentiment from text"""
    
    NEGATIVE_PATTERNS = [
        "壞了", "爛", "太差", "不滿", "失望", "生氣", "怒",
        "terrible", "awful", "hate", "angry", "disappointed"
    ]
    
    VERY_NEGATIVE_PATTERNS = [
        "投訴", "檢舉", "告", "媒體", "律师",
        "lawsuit", "complaint", "sue", "media"
    ]
    
    POSITIVE_PATTERNS = [
        "謝謝", "很好", "棒", "喜歡", "满意",
        "thanks", "great", "love", "good", "excellent"
    ]
    
    def analyze(self, text: str) -> Sentiment:
        """Analyze sentiment"""
        text_lower = text.lower()
        
        # Check very negative first
        for pattern in self.VERY_NEGATIVE_PATTERNS:
            if pattern in text_lower:
                return Sentiment.VERY_NEGATIVE
        
        # Check negative
        for pattern in self.NEGATIVE_PATTERNS:
            if pattern in text_lower:
                return Sentiment.NEGATIVE
        
        # Check positive
        for pattern in self.POSITIVE_PATTERNS:
            if pattern in text_lower:
                return Sentiment.POSITIVE
        
        return Sentiment.NEUTRAL


class ResponseGenerator:
    """Generate responses for customer queries"""
    
    TEMPLATES = {
        IntentType.REFUND: {
            "positive": "好的，我立刻為您處理退款。預計3-5個工作天到帳。",
            "neutral": "了解，我來幫您查詢退款進度。",
            "negative": "非常抱歉造成您的不便，我立即為您安排退款。",
            "very_negative": "我理解您非常不滿，我們會立即處理並補償您。"
        },
        IntentType.INQUIRY: {
            "positive": "很高興為您解答！",
            "neutral": "好的，讓我為您說明。",
            "negative": "我會盡快為您解答。",
            "very_negative": "非常抱歉造成困擾，讓我盡快為您說明。"
        },
        IntentType.TECH_SUPPORT: {
            "positive": "我來幫您解決這個問題！",
            "neutral": "讓我檢查一下。",
            "negative": "抱歉造成不便，我來幫您處理。",
            "very_negative": "這是我們的疏失，非常抱歉，我立刻幫您修復。"
        },
    }
    
    def generate(
        self,
        intent: IntentType,
        sentiment: Sentiment,
        custom_message: str = None
    ) -> str:
        """Generate response based on intent and sentiment"""
        if custom_message:
            return custom_message
        
        templates = self.TEMPLATES.get(intent, {})
        return templates.get(sentiment.value, "感謝您的來訊，我會盡快處理。")


class EscalationManager:
    """Manage human escalation"""
    
    def should_escalate(
        self,
        sentiment: Sentiment,
        retry_count: int = 0,
        threshold: float = 0.3
    ) -> bool:
        """Determine if should escalate to human"""
        # Escalate if very negative
        if sentiment == Sentiment.VERY_NEGATIVE:
            return True
        
        # Escalate if negative and retried
        if sentiment == Sentiment.NEGATIVE and retry_count >= 2:
            return True
        
        # Check threshold
        if sentiment == Sentiment.NEGATIVE:
            return threshold < 0.5
        
        return False


class CustomerServiceAgent:
    """
    Customer Service AI Agent.
    
    Usage:
        agent = CustomerServiceAgent(knowledge_base="docs/")
        result = agent.handle("我收到的商品壞了")
    """
    
    def __init__(
        self,
        knowledge_base: str = None,
        escalation_threshold: float = 0.3,
        language: str = "zh-TW"
    ):
        self.knowledge_base = knowledge_base
        self.escalation_threshold = escalation_threshold
        self.language = language
        
        # Components
        self.intent_classifier = IntentClassifier()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.response_generator = ResponseGenerator()
        self.escalation_manager = EscalationManager()
        
        logger.info(f"CustomerServiceAgent initialized (KB: {knowledge_base})")
    
    def handle(self, query: str) -> Dict[str, Any]:
        """Handle customer query"""
        # 1. Classify intent
        intent = self.intent_classifier.classify(query)
        
        # 2. Analyze sentiment
        sentiment = self.sentiment_analyzer.analyze(query)
        
        # 3. Check if should escalate
        should_escalate = self.escalation_manager.should_escalate(
            sentiment,
            threshold=self.escalation_threshold
        )
        
        # 4. Generate response
        response = self.response_generator.generate(intent, sentiment)
        
        result = {
            "query": query,
            "intent": intent.value,
            "sentiment": sentiment.value,
            "response": response,
            "escalate": should_escalate,
            "language": self.language
        }
        
        logger.info(f"Handled query: intent={intent.value}, sentiment={sentiment.value}")
        
        return result


class LegalAgent:
    """
    Legal AI Agent for contract analysis and document generation.
    
    Usage:
        legal = LegalAgent(jurisdiction="TW", practice_area="contract")
        analysis = legal.analyze_contract("agreement.txt")
    """
    
    def __init__(
        self,
        jurisdiction: str = "TW",
        practice_area: str = "contract"
    ):
        self.jurisdiction = jurisdiction
        self.practice_area = practice_area
        
        logger.info(f"LegalAgent initialized ({jurisdiction}, {practice_area})")
    
    def analyze_contract(self, text: str) -> Dict[str, Any]:
        """Analyze contract for risks"""
        risks = []
        
        # Common risk patterns
        risk_patterns = {
            "unlimited_liability": ["無限責任", "unlimited liability"],
            "auto_renewal": ["自動續約", "auto-renewal"],
            "unilateral_termination": ["單方面終止", "unilateral termination"],
            "indemnity": ["賠償責任", "indemnify"],
            "jurisdiction": ["管轄權", "jurisdiction"],
        }
        
        text_lower = text.lower()
        
        for risk_type, patterns in risk_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    risks.append({
                        "type": risk_type,
                        "severity": "high" if risk_type in ["unlimited_liability", "unilateral_termination"] else "medium",
                        "description": f"Found potential {risk_type} clause"
                    })
        
        return {
            "jurisdiction": self.jurisdiction,
            "risks": risks,
            "risk_score": len(risks) * 20,  # Simple scoring
            "recommendations": self._generate_recommendations(risks)
        }
    
    def _generate_recommendations(self, risks: List[Dict]) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []
        
        for risk in risks:
            if risk["type"] == "unlimited_liability":
                recommendations.append("建議加入責任上限條款")
            elif risk["type"] == "auto_renewal":
                recommendations.append("建議改為需雙方同意續約")
            elif risk["type"] == "unilateral_termination":
                recommendations.append("建議加入正當理由終止條款")
        
        return recommendations


# CLI entry point
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Vertical Domain Templates")
    parser.add_argument("command", choices=["init", "run"])
    parser.add_argument("--type", choices=["cs", "legal"], help="Agent type")
    parser.add_argument("--input", help="Query text")
    parser.add_argument("--kb", help="Knowledge base path")
    
    args = parser.parse_args()
    
    if args.command == "init":
        if args.type == "cs":
            agent = CustomerServiceAgent(knowledge_base=args.kb)
            print(f"Initialized CustomerServiceAgent (KB: {args.kb})")
        elif args.type == "legal":
            agent = LegalAgent()
            print("Initialized LegalAgent")
    
    elif args.command == "run":
        if args.type == "cs":
            agent = CustomerServiceAgent()
            result = agent.handle(args.input)
            print(result)
