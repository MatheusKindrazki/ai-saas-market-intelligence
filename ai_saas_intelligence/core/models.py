from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class MonetizationModel(str, Enum):
    """Monetization models for SaaS products"""
    SUBSCRIPTION = "subscription"
    USAGE_BASED = "usage_based"
    FREEMIUM = "freemium"
    ENTERPRISE_LICENSE = "enterprise_license"
    MARKETPLACE = "marketplace"
    HYBRID = "hybrid"


class MarketSegment(str, Enum):
    """Market segments for AI SaaS opportunities"""
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    E_COMMERCE = "e_commerce"
    EDUCATION = "education"
    LEGAL = "legal"
    MARKETING = "marketing"
    HR = "hr"
    DEVELOPMENT = "development"
    OPERATIONS = "operations"
    CUSTOMER_SERVICE = "customer_service"


@dataclass
class MarketTrend:
    """Represents a current or emerging market trend"""
    name: str
    description: str
    growth_potential: float  # 0-1 scale
    market_size_estimate: str
    key_technologies: List[str]
    adoption_stage: str  # early, growing, mature


@dataclass
class PainPoint:
    """Represents a market pain point or gap"""
    industry: MarketSegment
    problem: str
    severity: float  # 0-1 scale
    current_solutions: List[str]
    why_insufficient: str


@dataclass
class ProductIdea:
    """Represents a potential AI SaaS product idea"""
    name: str
    description: str
    target_audience: str
    primary_pain_point: PainPoint
    monetization_model: MonetizationModel
    pricing_strategy: str
    key_features: List[str]
    technical_requirements: List[str]
    differentiation: str
    estimated_mvp_months: int


@dataclass
class Competitor:
    """Represents a market competitor"""
    name: str
    market_share: float
    strengths: List[str]
    weaknesses: List[str]
    pricing_model: str


@dataclass
class MarketAnalysis:
    """Complete market analysis for a trend"""
    trend: MarketTrend
    pain_points: List[PainPoint]
    product_ideas: List[ProductIdea]
    competitors: List[Competitor]
    go_to_market_strategy: Dict[str, str]
    market_entry_difficulty: float  # 0-1 scale


@dataclass
class GoToMarketStrategy:
    """Go-to-market strategy for a product"""
    target_segments: List[str]
    acquisition_channels: List[str]
    pricing_tier_suggestions: List[Dict[str, str]]
    marketing_angle: str
    early_adopter_profile: str
    partnership_opportunities: List[str]
