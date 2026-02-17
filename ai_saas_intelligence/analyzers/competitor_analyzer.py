"""Competitive landscape analyzer for market positioning"""

from typing import List, Dict
from ..core.models import Competitor, MarketTrend


class CompetitorAnalyzer:
    """Analyzes competitive landscape for AI SaaS opportunities"""
    
    def __init__(self):
        self.competitors_db = self._initialize_competitors_database()
    
    def _initialize_competitors_database(self) -> Dict[str, List[Competitor]]:
        """Initialize comprehensive competitors database by trend"""
        return {
            "Generative AI for Content Creation": [
                Competitor(
                    name="Jasper AI",
                    market_share=0.25,
                    strengths=["Strong brand presence", "Marketing-focused features", "Good UI/UX"],
                    weaknesses=["Generic outputs", "Limited brand voice learning", "High pricing"],
                    pricing_model="Subscription ($49-$125/month)"
                ),
                Competitor(
                    name="Copy.ai",
                    market_share=0.18,
                    strengths=["Free tier available", "Easy to use", "Good templates"],
                    weaknesses=["Quality inconsistency", "Limited customization", "No brand consistency"],
                    pricing_model="Freemium ($36-$186/month)"
                ),
                Competitor(
                    name="CopySmith",
                    market_share=0.12,
                    strengths=["E-commerce focus", "Product description strength"],
                    weaknesses=["Limited use cases", "Smaller feature set"],
                    pricing_model="Subscription ($19-$59/month)"
                )
            ],
            "AI-Powered Customer Intelligence": [
                Competitor(
                    name="Mixpanel",
                    market_share=0.30,
                    strengths=["Strong analytics", "Large user base", "Good integrations"],
                    weaknesses=["Limited AI predictions", "Steep learning curve"],
                    pricing_model="Usage-based (starts at $25/month)"
                ),
                Competitor(
                    name="Amplitude",
                    market_share=0.25,
                    strengths=["Product analytics focus", "Good cohort analysis"],
                    weaknesses=["Limited churn prediction", "Complex setup"],
                    pricing_model="Usage-based (custom pricing)"
                ),
                Competitor(
                    name="Heap",
                    market_share=0.15,
                    strengths=["Automatic event tracking"],
                    weaknesses=["Limited AI features", "Data retention costs"],
                    pricing_model="Usage-based (starts at $3,600/year)"
                )
            ],
            "Automated Code Generation & DevOps": [
                Competitor(
                    name="GitHub Copilot",
                    market_share=0.45,
                    strengths=["Deep IDE integration", "Large training data", "Microsoft backing"],
                    weaknesses=["Security concerns", "Limited code review features"],
                    pricing_model="Subscription ($10-$19/user/month)"
                ),
                Competitor(
                    name="Tabnine",
                    market_share=0.20,
                    strengths=["Privacy-focused", "Enterprise features"],
                    weaknesses=["Smaller training dataset", "Less seamless integration"],
                    pricing_model="Subscription ($12-$49/user/month)"
                ),
                Competitor(
                    name="CodeT5",
                    market_share=0.10,
                    strengths=["Open source", "Customizable"],
                    weaknesses=["No commercial support", "Requires setup"],
                    pricing_model="Open source"
                )
            ],
            "AI in Healthcare Diagnostics": [
                Competitor(
                    name="PathAI",
                    market_share=0.35,
                    strengths=["Strong pathology focus", "Regulatory approvals"],
                    weaknesses=["Limited imaging modalities", "High cost"],
                    pricing_model="Enterprise (custom pricing)"
                ),
                Competitor(
                    name="Aidoc",
                    market_share=0.28,
                    strengths=["Radiology focus", "FDA cleared solutions"],
                    weaknesses=["Limited to specific conditions"],
                    pricing_model="Enterprise (per-scan pricing)"
                ),
                Competitor(
                    name="Arterys",
                    market_share=0.15,
                    strengths=["Cloud platform", "Cardiovascular focus"],
                    weaknesses=["Limited adoption", "Specialized use cases"],
                    pricing_model="Enterprise licensing"
                )
            ],
            "Financial Fraud Detection AI": [
                Competitor(
                    name="Sift",
                    market_share=0.32,
                    strengths=["Large customer base", "Real-time capabilities"],
                    weaknesses=["High false positive rates", "Complex setup"],
                    pricing_model="Usage-based (starts at $500/month)"
                ),
                Competitor(
                    name="Forter",
                    market_share=0.25,
                    strengths=["E-commerce focus", "Strong fraud guarantees"],
                    weaknesses=["Limited to e-commerce", "Premium pricing"],
                    pricing_model="Commission (0.5-1% of protected revenue)"
                ),
                Competitor(
                    name="Riskified",
                    market_share=0.20,
                    strengths=["Chargeback guarantees", "Merchant integration"],
                    weaknesses=["Limited fraud insights", "Black-box decisions"],
                    pricing_model="Commission-based"
                )
            ],
            "AI-Powered Legal Document Analysis": [
                Competitor(
                    name="Kira Systems",
                    market_share=0.30,
                    strengths=["Strong law firm adoption", "Machine learning focus"],
                    weaknesses=["High pricing", "Complex implementation"],
                    pricing_model="Enterprise ($50,000+/year)"
                ),
                Competitor(
                    name="Luminance",
                    market_share=0.25,
                    strengths=["User-friendly interface", "Good support"],
                    weaknesses=["Limited template library", "Smaller training data"],
                    pricing_model="Subscription (£3,000-£10,000/month)"
                ),
                Competitor(
                    name="LawGeex",
                    market_share=0.15,
                    strengths=["Contract review focus", "Playbook features"],
                    weaknesses=["Limited to contracts", "Narrow scope"],
                    pricing_model="Subscription (custom pricing)"
                )
            ],
            "Intelligent HR & Talent Acquisition": [
                Competitor(
                    name="Eightfold AI",
                    market_share=0.28,
                    strengths=["Deep learning matching", "Talent pool focus"],
                    weaknesses=["Expensive", "Complex implementation"],
                    pricing_model="Enterprise (custom pricing)"
                ),
                Competitor(
                    name="Phenom",
                    market_share=0.22,
                    strengths=["End-to-end platform", "Good UI"],
                    weaknesses=["Limited AI depth", "Best for large enterprises"],
                    pricing_model="Enterprise licensing"
                ),
                Competitor(
                    name="HireVue",
                    market_share=0.18,
                    strengths=["Video interview focus", "Assessment tools"],
                    weaknesses=["Limited matching AI", "Privacy concerns"],
                    pricing_model="Per-candidate pricing"
                )
            ],
            "AI-Driven Supply Chain Optimization": [
                Competitor(
                    name="FourKites",
                    market_share=0.35,
                    strengths=["Real-time tracking", "Large carrier network"],
                    weaknesses=["Limited predictive AI", "Focus on tracking not optimization"],
                    pricing_model="Enterprise licensing"
                ),
                Competitor(
                    name="Project44",
                    market_share=0.30,
                    strengths=["Strong integrations", "Global coverage"],
                    weaknesses=["Limited optimization features", "High entry cost"],
                    pricing_model="Enterprise (custom pricing)"
                ),
                Competitor(
                    name="Kinaxis",
                    market_share=0.20,
                    strengths=["Planning focus", "Optimization engine"],
                    weaknesses=["Legacy UI", "Steep learning curve"],
                    pricing_model="Enterprise licensing"
                )
            ],
            "Personalized Learning Platforms": [
                Competitor(
                    name="Knewton",
                    market_share=0.25,
                    strengths=["Adaptive learning pioneer", "Strong partnerships"],
                    weaknesses=["Limited content creation", "Focus on publishers"],
                    pricing_model="Enterprise licensing"
                ),
                Competitor(
                    name="DreamBox",
                    market_share=0.22,
                    strengths=["K-12 focus", "Good engagement"],
                    weaknesses=["Limited age range", "No higher ed"],
                    pricing_model="Per-student pricing"
                ),
                Competitor(
                    name="Carnegie Learning",
                    market_share=0.18,
                    strengths=["Math focus", "Research-backed"],
                    weaknesses=["Subject limited", "Traditional approach"],
                    pricing_model="Per-student licensing"
                )
            ],
            "AI Marketing Automation & Attribution": [
                Competitor(
                    name="HubSpot",
                    market_share=0.35,
                    strengths=["All-in-one platform", "Strong ecosystem"],
                    weaknesses=["Limited AI depth", "Premium pricing at scale"],
                    pricing_model="Tiered ($45-$3,200/month)"
                ),
                Competitor(
                    name="Marketo",
                    market_share=0.25,
                    strengths=["Enterprise features", "Adobe integration"],
                    weaknesses=["Complex interface", "Steep learning curve"],
                    pricing_model="Enterprise ($1,195-$3,195/month)"
                ),
                Competitor(
                    name="Braze (formerly Appboy)",
                    market_share=0.20,
                    strengths=["Customer engagement focus", "Good mobile features"],
                    weaknesses=["Limited attribution", "Best for mobile"],
                    pricing_model="Usage-based (starts at $1,000/month)"
                )
            ]
        }
    
    def get_competitors_for_trend(self, trend_name: str) -> List[Competitor]:
        """Get competitors for a specific market trend"""
        # Try exact match first
        if trend_name in self.competitors_db:
            return self.competitors_db[trend_name]
        
        # Try partial match
        for key, competitors in self.competitors_db.items():
            if trend_name.lower() in key.lower() or key.lower() in trend_name.lower():
                return competitors
        
        return []
    
    def analyze_competitive_gap(self, trend_name: str, competitor: Competitor) -> Dict[str, str]:
        """Analyze competitive gaps and opportunities"""
        return {
            "competitor": competitor.name,
            "market_share": f"{competitor.market_share * 100:.1f}%",
            "key_weaknesses": competitor.weaknesses,
            "pricing_gap": self._analyze_pricing_gap(competitor),
            "feature_opportunities": self._identify_feature_opportunities(competitor),
            "differentiation_strategy": self._suggest_differentiation(competitor)
        }
    
    def _analyze_pricing_gap(self, competitor: Competitor) -> str:
        """Analyze pricing gaps"""
        pricing_lower = competitor.pricing_model.lower()
        
        if "free" in pricing_lower:
            return "Opportunity: Freemium with premium features could capture value"
        elif "enterprise" in pricing_lower or "custom" in pricing_lower:
            return "Opportunity: Transparent, predictable pricing for mid-market"
        elif "commission" in pricing_lower:
            return "Opportunity: Flat subscription could be more predictable for customers"
        elif "$" in pricing_lower:
            if "$500" in pricing_lower or "$1000" in pricing_lower or "$50,000" in pricing_lower:
                return "Opportunity: Lower-cost SMB offering"
            else:
                return "Opportunity: Enterprise-grade features at competitive price"
        
        return "Pricing analysis needed"
    
    def _identify_feature_opportunities(self, competitor: Competitor) -> List[str]:
        """Identify feature opportunities based on competitor weaknesses"""
        opportunities = []
        
        for weakness in competitor.weaknesses:
            if "generic" in weakness.lower():
                opportunities.append("Personalized, custom outputs")
            elif "limited" in weakness.lower():
                opportunities.append("Broader feature coverage")
            elif "complex" in weakness.lower() or "learning curve" in weakness.lower():
                opportunities.append("Simplified user experience")
            elif "expensive" in weakness.lower() or "pricing" in weakness.lower():
                opportunities.append("Competitive pricing tiers")
            elif "integration" in weakness.lower():
                opportunities.append("Deep third-party integrations")
        
        return opportunities if opportunities else ["Innovative features", "Better UX", "Superior performance"]
    
    def _suggest_differentiation(self, competitor: Competitor) -> str:
        """Suggest differentiation strategy"""
        strengths_str = " ".join(competitor.strengths).lower()
        
        if "brand" in strengths_str or "large" in strengths_str:
            return "Differentiate through innovation and niche focus"
        elif "analytics" in strengths_str:
            return "Differentiate through actionable insights and recommendations"
        elif "focus" in strengths_str:
            return "Differentiate through broader platform and all-in-one solution"
        
        return "Differentiate through superior AI performance and user experience"
    
    def get_market_concentration(self, trend_name: str) -> str:
        """Assess market concentration (fragmented, consolidated, etc.)"""
        competitors = self.get_competitors_for_trend(trend_name)
        
        if not competitors:
            return "Unknown - no competitor data"
        
        # Calculate Herfindahl-Hirschman Index (HHI)
        hhi = sum(c.market_share ** 2 for c in competitors)
        
        if hhi < 0.15:
            return "Fragmented - opportunity for new entrants"
        elif hhi < 0.25:
            return "Moderately concentrated - room for differentiation"
        else:
            return "Concentrated - need strong differentiation"
    
    def get_swot_summary(self, trend_name: str) -> Dict[str, List[str]]:
        """Generate SWOT summary for market entry"""
        competitors = self.get_competitors_for_trend(trend_name)
        
        if not competitors:
            return {}
        
        all_strengths = [s for c in competitors for s in c.strengths]
        all_weaknesses = [w for c in competitors for w in c.weaknesses]
        
        # Extract unique strengths and weaknesses
        unique_strengths = list(set(all_strengths))[:5]
        unique_weaknesses = list(set(all_weaknesses))[:5]
        
        return {
            "Market_Threats": unique_strengths,  # What competitors do well
            "Market_Opportunities": unique_weaknesses,  # What competitors lack
            "Potential_Strengths": ["Better AI performance", "Superior UX", "Competitive pricing"],
            "Potential_Weaknesses": ["New brand", "Limited resources", "Unproven track record"]
        }
