"""AI SaaS Market Intelligence Platform - Actionable market analysis for AI-powered SaaS products"""

__version__ = "1.0.0"
__author__ = "AI SaaS Intelligence Team"

from .core.models import (
    MarketTrend,
    PainPoint,
    ProductIdea,
    Competitor,
    MarketAnalysis,
    GoToMarketStrategy,
    MonetizationModel,
    MarketSegment
)

from .analyzers.trend_analyzer import TrendAnalyzer
from .analyzers.pain_point_analyzer import PainPointAnalyzer
from .analyzers.competitor_analyzer import CompetitorAnalyzer
from .generators.product_idea_generator import ProductIdeaGenerator
from .strategies.gtm_strategy import GTMStrategyGenerator

__all__ = [
    'MarketTrend',
    'PainPoint',
    'ProductIdea',
    'Competitor',
    'MarketAnalysis',
    'GoToMarketStrategy',
    'MonetizationModel',
    'MarketSegment',
    'TrendAnalyzer',
    'PainPointAnalyzer',
    'CompetitorAnalyzer',
    'ProductIdeaGenerator',
    'GTMStrategyGenerator'
]
