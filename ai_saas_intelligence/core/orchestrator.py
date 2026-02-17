"""Main orchestrator for AI SaaS Market Intelligence platform"""

from typing import List, Dict, Optional
from ..analyzers.trend_analyzer import TrendAnalyzer
from ..analyzers.pain_point_analyzer import PainPointAnalyzer
from ..analyzers.competitor_analyzer import CompetitorAnalyzer
from ..generators.product_idea_generator import ProductIdeaGenerator
from ..strategies.gtm_strategy import GTMStrategyGenerator
from ..core.models import MarketAnalysis, ProductIdea, MarketTrend, MarketSegment


class MarketIntelligenceOrchestrator:
    """Orchestrates all market intelligence components"""
    
    def __init__(self):
        self.trend_analyzer = TrendAnalyzer()
        self.pain_point_analyzer = PainPointAnalyzer()
        self.competitor_analyzer = CompetitorAnalyzer()
        self.idea_generator = ProductIdeaGenerator()
        self.gtm_generator = GTMStrategyGenerator()
    
    def generate_comprehensive_report(self, trend_name: Optional[str] = None) -> Dict:
        """Generate comprehensive market intelligence report"""
        if trend_name:
            # Analyze specific trend
            return self._generate_trend_report(trend_name)
        else:
            # Generate overview report with top opportunities
            return self._generate_overview_report()
    
    def _generate_trend_report(self, trend_name: str) -> Dict:
        """Generate detailed report for a specific trend"""
        # Get trend analysis
        trend_analysis = self.trend_analyzer.analyze_trend_potential(trend_name)
        
        # Find related pain points
        pain_points = self._find_related_pain_points(trend_name)
        
        # Generate product ideas
        ideas = []
        for pain_point in pain_points:
            ideas.extend(self.idea_generator.generate_ideas_for_pain_point(pain_point))
        
        # Get competitor analysis
        competitors = self.competitor_analyzer.get_competitors_for_trend(trend_name)
        swot = self.competitor_analyzer.get_swot_summary(trend_name)
        market_concentration = self.competitor_analyzer.get_market_concentration(trend_name)
        
        # Generate GTM strategies for top ideas
        top_ideas = sorted(ideas, key=lambda x: self.idea_generator.score_idea_potential(x), reverse=True)[:3]
        gtm_strategies = [self.gtm_generator.generate_gtm_strategy(idea) for idea in top_ideas]
        
        return {
            "trend_analysis": trend_analysis,
            "pain_points": [
                {
                    "industry": p.industry.value,
                    "problem": p.problem,
                    "severity": f"{p.severity:.0%}",
                    "gap": p.why_insufficient
                }
                for p in pain_points[:5]
            ],
            "product_ideas": [
                {
                    "name": idea.name,
                    "description": idea.description,
                    "target_audience": idea.target_audience,
                    "monetization": idea.monetization_model.value,
                    "pricing": idea.pricing_strategy,
                    "mvp_months": idea.estimated_mvp_months,
                    "differentiation": idea.differentiation,
                    "potential_score": f"{self.idea_generator.score_idea_potential(idea):.1%}"
                }
                for idea in top_ideas
            ],
            "competitive_landscape": {
                "market_concentration": market_concentration,
                "competitors": [
                    {
                        "name": c.name,
                        "market_share": f"{c.market_share:.0%}",
                        "strengths": c.strengths,
                        "weaknesses": c.weaknesses,
                        "pricing": c.pricing_model
                    }
                    for c in competitors[:3]
                ],
                "swot_summary": swot
            },
            "go_to_market": [
                {
                    "idea_name": idea.name,
                    "target_segments": gtm.target_segments,
                    "channels": gtm.acquisition_channels,
                    "marketing_angle": gtm.marketing_angle,
                    "early_adopter": gtm.early_adopter_profile,
                    "partnerships": gtm.partnership_opportunities,
                    "pricing_tiers": gtm.pricing_tier_suggestions
                }
                for idea, gtm in zip(top_ideas, gtm_strategies)
            ]
        }
    
    def generate_overview_report(self) -> Dict:
        """Generate overview report with top opportunities"""
        # Get top trends
        top_trends = self.trend_analyzer.get_top_opportunities(5)
        
        # Get high severity pain points
        high_severity_pain = self.pain_point_analyzer.get_high_severity_pain_points(0.8)
        
        # Get top product ideas
        top_ideas = self.idea_generator.get_top_ideas(5)
        
        return {
            "executive_summary": {
                "total_trends_analyzed": len(self.trend_analyzer.get_all_trends()),
                "high_severity_pain_points": len(high_severity_pain),
                "product_opportunities": len(self.idea_generator.generate_all_ideas())
            },
            "top_market_opportunities": [
                {
                    "trend": trend.name,
                    "growth_potential": f"{trend.growth_potential:.0%}",
                    "market_size": trend.market_size_estimate,
                    "adoption_stage": trend.adoption_stage,
                    "key_tech": trend.key_technologies[:3]
                }
                for trend in top_trends
            ],
            "critical_market_gaps": [
                {
                    "industry": p.industry.value,
                    "problem": p.problem,
                    "severity": f"{p.severity:.0%}",
                    "opportunity_rating": self.pain_point_analyzer._rate_opportunity(p)
                }
                for p in high_severity_pain[:8]
            ],
            "top_product_ideas": [
                {
                    "name": idea.name,
                    "description": idea.description,
                    "target_audience": idea.target_audience,
                    "monetization": idea.monetization_model.value,
                    "pricing": idea.pricing_strategy,
                    "mvp_months": idea.estimated_mvp_months,
                    "potential_score": f"{score:.1%}",
                    "key_differentiators": idea.differentiation
                }
                for idea, score in top_ideas
            ]
        }
    
    def _find_related_pain_points(self, trend_name: str) -> List:
        """Find pain points related to a trend"""
        trend_lower = trend_name.lower()
        all_pain = self.pain_point_analyzer.pain_points_db
        
        # Map trends to industries
        industry_map = {
            "healthcare": MarketSegment.HEALTHCARE,
            "medical": MarketSegment.HEALTHCARE,
            "diagnostic": MarketSegment.HEALTHCARE,
            "finance": MarketSegment.FINANCE,
            "fraud": MarketSegment.FINANCE,
            "payment": MarketSegment.FINANCE,
            "ecommerce": MarketSegment.E_COMMERCE,
            "marketing": MarketSegment.MARKETING,
            "content": MarketSegment.MARKETING,
            "legal": MarketSegment.LEGAL,
            "contract": MarketSegment.LEGAL,
            "hr": MarketSegment.HR,
            "hiring": MarketSegment.HR,
            "recruitment": MarketSegment.HR,
            "development": MarketSegment.DEVELOPMENT,
            "code": MarketSegment.DEVELOPMENT,
            "operations": MarketSegment.OPERATIONS,
            "supply": MarketSegment.OPERATIONS,
            "inventory": MarketSegment.OPERATIONS,
            "education": MarketSegment.EDUCATION,
            "learning": MarketSegment.EDUCATION,
            "customer": MarketSegment.CUSTOMER_SERVICE,
            "support": MarketSegment.CUSTOMER_SERVICE
        }
        
        related = []
        for keyword, industry in industry_map.items():
            if keyword in trend_lower:
                related.extend(self.pain_point_analyzer.get_pain_points_by_industry(industry))
                break
        
        return related if related else []
    
    def get_quick_recommendations(self, count: int = 3) -> List[Dict]:
        """Get quick recommendations for highest-potential opportunities"""
        top_ideas = self.idea_generator.get_top_ideas(count * 2)  # Get more to filter
        
        recommendations = []
        for idea, score in top_ideas:
            if len(recommendations) >= count:
                break
            
            gtm = self.gtm_generator.generate_gtm_strategy(idea)
            
            recommendations.append({
                "product": idea.name,
                "why_now": idea.differentiation,
                "market_fit": f"{score:.0%}",
                "time_to_market": f"{idea.estimated_mvp_months} months",
                "first_movers": idea.target_audience,
                "monetization": idea.monetization_model.value,
                "starting_price": idea.pricing_strategy.split(",")[0],
                "entry_strategy": gtm.acquisition_channels[0]
            })
        
        return recommendations
    
    def analyze_monetization_models(self) -> Dict[str, List[str]]:
        """Analyze which monetization models work for different markets"""
        ideas = self.idea_generator.generate_all_ideas()
        
        model_analysis = {}
        for idea in ideas:
            model = idea.monetization_model.value
            if model not in model_analysis:
                model_analysis[model] = []
            
            if len(model_analysis[model]) < 3:  # Limit examples
                model_analysis[model].append(idea.name)
        
        # Add insights
        insights = {
            "subscription": "Best for predictable revenue and SaaS adoption",
            "usage_based": "Ideal for variable usage patterns and lower entry barrier",
            "freemium": "Effective for virality and self-service growth",
            "enterprise_license": "High-value, complex sales for large organizations",
            "hybrid": "Flexible approach for diverse customer segments"
        }
        
        return {
            "models": model_analysis,
            "insights": insights
        }
