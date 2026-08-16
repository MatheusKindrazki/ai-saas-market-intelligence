"""Market trend analyzer for AI SaaS opportunities"""

from typing import List
from ..core.models import MarketTrend, MarketSegment


class TrendAnalyzer:
    """Analyzes current and emerging market trends in AI SaaS"""
    
    def __init__(self):
        self.trends_db = self._initialize_trends_database()
    
    def _initialize_trends_database(self) -> List[MarketTrend]:
        """Initialize the comprehensive trends database"""
        return [
            MarketTrend(
                name="Generative AI for Content Creation",
                description="AI-powered tools that generate text, images, video, and audio content at scale",
                growth_potential=0.92,
                market_size_estimate="$40B by 2027",
                key_technologies=["LLMs", "Diffusion Models", "Transformers", "Multimodal AI"],
                adoption_stage="growing"
            ),
            MarketTrend(
                name="AI-Powered Customer Intelligence",
                description="Deep customer behavior analysis using AI for personalization and retention",
                growth_potential=0.88,
                market_size_estimate="$35B by 2026",
                key_technologies=["Predictive Analytics", "NLP", "Behavioral ML", "Sentiment Analysis"],
                adoption_stage="growing"
            ),
            MarketTrend(
                name="Automated Code Generation & DevOps",
                description="AI tools that write, review, and optimize code plus automate DevOps workflows",
                growth_potential=0.90,
                market_size_estimate="$30B by 2028",
                key_technologies=["Code LLMs", "Static Analysis AI", "Pipeline Optimization", "AI Testing"],
                adoption_stage="growing"
            ),
            MarketTrend(
                name="AI in Healthcare Diagnostics",
                description="AI-powered medical imaging analysis and diagnostic support tools",
                growth_potential=0.85,
                market_size_estimate="$25B by 2027",
                key_technologies=["Computer Vision", "Medical Imaging AI", "Predictive Diagnostics", "NLP"],
                adoption_stage="early"
            ),
            MarketTrend(
                name="Financial Fraud Detection AI",
                description="Real-time fraud detection and risk assessment using machine learning",
                growth_potential=0.82,
                market_size_estimate="$20B by 2026",
                key_technologies=["Anomaly Detection", "Graph ML", "Real-time Analytics", "Pattern Recognition"],
                adoption_stage="growing"
            ),
            MarketTrend(
                name="AI-Powered Legal Document Analysis",
                description="Automated contract review, legal research, and document intelligence",
                growth_potential=0.80,
                market_size_estimate="$18B by 2026",
                key_technologies=["Legal NLP", "Document Understanding", "Knowledge Graphs", "NER"],
                adoption_stage="growing"
            ),
            MarketTrend(
                name="Intelligent HR & Talent Acquisition",
                description="AI tools for recruiting, candidate matching, and employee retention analytics",
                growth_potential=0.78,
                market_size_estimate="$15B by 2027",
                key_technologies=["Resume Parsing AI", "Matching Algorithms", "Predictive HR Analytics", "NLP"],
                adoption_stage="growing"
            ),
            MarketTrend(
                name="AI-Driven Supply Chain Optimization",
                description="Predictive logistics, inventory management, and demand forecasting",
                growth_potential=0.83,
                market_size_estimate="$22B by 2026",
                key_technologies=["Predictive Analytics", "Optimization ML", "IoT Integration", "Demand Forecasting"],
                adoption_stage="early"
            ),
            MarketTrend(
                name="Personalized Learning Platforms",
                description="AI-powered educational content adaptation and learning path optimization",
                growth_potential=0.81,
                market_size_estimate="$25B by 2027",
                key_technologies=["Adaptive Learning AI", "Knowledge Tracing", "Content Generation", "Assessment AI"],
                adoption_stage="growing"
            ),
            MarketTrend(
                name="AI Marketing Automation & Attribution",
                description="Automated campaign optimization, content generation, and ROI attribution",
                growth_potential=0.86,
                market_size_estimate="$32B by 2026",
                key_technologies=["Generative Marketing AI", "Attribution Modeling", "Predictive Analytics", "NLP"],
                adoption_stage="growing"
            )
        ]
    
    def get_all_trends(self) -> List[MarketTrend]:
        """Get all available market trends"""
        return self.trends_db
    
    def get_trends_by_growth_potential(self, min_score: float = 0.8) -> List[MarketTrend]:
        """Filter trends by minimum growth potential score"""
        return [t for t in self.trends_db if t.growth_potential >= min_score]
    
    def get_trends_by_adoption_stage(self, stage: str) -> List[MarketTrend]:
        """Filter trends by adoption stage"""
        stage = stage.lower()
        return [t for t in self.trends_db if t.adoption_stage == stage]
    
    def get_trends_by_technology(self, technology: str) -> List[MarketTrend]:
        """Find trends that use specific technology"""
        technology_lower = technology.lower()
        return [
            t for t in self.trends_db 
            if any(technology_lower in tech.lower() for tech in t.key_technologies)
        ]
    
    def get_top_opportunities(self, count: int = 5) -> List[MarketTrend]:
        """Get top opportunities sorted by growth potential"""
        return sorted(self.trends_db, key=lambda x: x.growth_potential, reverse=True)[:count]
    
    def analyze_trend_potential(self, trend_name: str) -> dict:
        """Deep analysis of a specific trend's potential"""
        trends = [t for t in self.trends_db if t.name.lower() == trend_name.lower()]
        if not trends:
            raise ValueError(f"Trend '{trend_name}' not found in database")
        
        trend = trends[0]
        return {
            "name": trend.name,
            "growth_score": trend.growth_potential,
            "growth_rating": self._get_growth_rating(trend.growth_potential),
            "market_size": trend.market_size_estimate,
            "adopion_stage": trend.adoption_stage,
            "opportunity_level": self._assess_opportunity_level(trend),
            "key_differentiators": trend.key_technologies[:3]
        }
    
    def _get_growth_rating(self, score: float) -> str:
        """Convert growth score to rating"""
        if score >= 0.9:
            return "Exceptional"
        elif score >= 0.8:
            return "High"
        elif score >= 0.7:
            return "Moderate"
        else:
            return "Low"
    
    def _assess_opportunity_level(self, trend: MarketTrend) -> str:
        """Assess overall opportunity level considering multiple factors"""
        high_growth = trend.growth_potential >= 0.8
        early_growing = trend.adoption_stage in ["early", "growing"]
        
        if high_growth and early_growing:
            return "Prime Opportunity"
        elif high_growth:
            return "High Potential"
        elif early_growing:
            return "Emerging"
        else:
            return "Stable"
