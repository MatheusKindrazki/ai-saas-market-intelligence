"""Go-to-market strategy generator for AI SaaS products"""

from typing import List, Dict
from ..core.models import ProductIdea, GoToMarketStrategy


class GTMStrategyGenerator:
    """Generates go-to-market strategies for AI SaaS products"""
    
    def __init__(self):
        self.channel_strategies = self._initialize_channel_strategies()
        self.segmentation_rules = self._initialize_segmentation_rules()
    
    def _initialize_channel_strategies(self) -> Dict[str, dict]:
        """Initialize acquisition channel strategies"""
        return {
            "content_marketing": {
                "channels": ["SEO blog", "Whitepapers", "Case studies", "Webinars"],
                "time_to_result": "6-12 months",
                "cost": "Low to medium",
                "effectiveness": "High for B2B SaaS",
                "best_for": ["Content generation", "Marketing automation", "Developer tools"]
            },
            "paid_advertising": {
                "channels": ["Google Ads", "LinkedIn Ads", "Meta Ads", "Twitter/X"],
                "time_to_result": "Immediate",
                "cost": "High",
                "effectiveness": "Medium-high",
                "best_for": ["Customer intelligence", "HR tech", "E-commerce"]
            },
            "product_led_growth": {
                "channels": ["Free trial", "Freemium", "Self-service signup", "In-app referrals"],
                "time_to_result": "3-6 months",
                "cost": "Low",
                "effectiveness": "Very high for PLG products",
                "best_for": ["Developer tools", "Code review", "Content creation"]
            },
            "outbound_sales": {
                "channels": ["Cold email", "Cold calling", "LinkedIn outreach", "Account-based marketing"],
                "time_to_result": "3-6 months",
                "cost": "Medium-high",
                "effectiveness": "High for enterprise",
                "best_for": ["Enterprise fraud detection", "Supply chain", "Healthcare"]
            },
            "partnerships": {
                "channels": ["Platform partnerships", "Reseller agreements", "Technology alliances", "Consulting partners"],
                "time_to_result": "6-12 months",
                "cost": "Medium",
                "effectiveness": "High for established partners",
                "best_for": ["Legal tech", "Healthcare", "Finance"]
            },
            "community_building": {
                "channels": ["Discord/Slack communities", "GitHub open source", "Conferences", "Meetups"],
                "time_to_result": "6-18 months",
                "cost": "Low to medium",
                "effectiveness": "High for developer tools",
                "best_for": ["Developer tools", "Code generation", "DevOps"]
            }
        }
    
    def _initialize_segmentation_rules(self) -> Dict[str, dict]:
        """Initialize market segmentation rules"""
        return {
            "segment_by_company_size": {
                "startup": "1-50 employees, budget-conscious, tech-forward",
                "smb": "51-500 employees, value-focused, need efficiency",
                "mid_market": "501-2000 employees, growth-focused, integration needs",
                "enterprise": "2000+ employees, security-conscious, need compliance"
            },
            "segment_by_industry": {
                "healthcare": "Compliance-focused, long sales cycles, high value per customer",
                "finance": "Risk-averse, security-critical, regulatory requirements",
                "tech": "Early adopters, feature-focused, willing to try new tech",
                "retail_ecommerce": "ROI-focused, seasonal, competitive market"
            },
            "segment_by_technical_maturity": {
                "early_adopter": "Tech-savvy, willing to try beta, provide feedback",
                "mainstream": "Proven solution, references important, less risk-tolerant",
                "laggard": "Traditional, slow to adopt, need extensive proof"
            }
        }
    
    def generate_gtm_strategy(self, product_idea: ProductIdea) -> GoToMarketStrategy:
        """Generate comprehensive GTM strategy for a product idea"""
        # Determine target segments
        target_segments = self._determine_target_segments(product_idea)
        
        # Determine acquisition channels
        acquisition_channels = self._determine_acquisition_channels(product_idea)
        
        # Generate pricing tiers
        pricing_tier_suggestions = self._generate_pricing_tiers(product_idea)
        
        # Develop marketing angle
        marketing_angle = self._develop_marketing_angle(product_idea)
        
        # Define early adopter profile
        early_adopter_profile = self._define_early_adopter(product_idea)
        
        # Identify partnership opportunities
        partnership_opportunities = self._identify_partnerships(product_idea)
        
        return GoToMarketStrategy(
            target_segments=target_segments,
            acquisition_channels=acquisition_channels,
            pricing_tier_suggestions=pricing_tier_suggestions,
            marketing_angle=marketing_angle,
            early_adopter_profile=early_adopter_profile,
            partnership_opportunities=partnership_opportunities
        )
    
    def _determine_target_segments(self, idea: ProductIdea) -> List[str]:
        """Determine primary target market segments"""
        segments = []
        
        # Based on target audience text
        audience_lower = idea.target_audience.lower()
        
        if "enterprise" in audience_lower or "large" in audience_lower:
            segments.append("Enterprise (2000+ employees)")
        if "startup" in audience_lower or "small" in audience_lower:
            segments.append("Startup/SMB (1-500 employees)")
        if "mid" in audience_lower:
            segments.append("Mid-Market (500-2000 employees)")
        
        # Based on industry
        if any(ind in audience_lower for ind in ["hospital", "healthcare", "medical"]):
            segments.append("Healthcare Industry")
        if any(ind in audience_lower for ind in ["bank", "fintech", "finance", "payment"]):
            segments.append("Financial Services")
        if any(ind in audience_lower for ind in ["marketing", "agency", "brand"]):
            segments.append("Marketing & Advertising")
        if any(ind in audience_lower for ind in ["developer", "engineering", "software"]):
            segments.append("Software Development")
        
        # Default segments if none identified
        if not segments:
            segments = ["Mid-Market (500-2000 employees)", "Enterprise (2000+ employees)"]
        
        return segments[:3]  # Return top 3 segments
    
    def _determine_acquisition_channels(self, idea: ProductIdea) -> List[str]:
        """Determine best acquisition channels"""
        channels = []
        idea_lower = idea.description.lower() + " " + idea.target_audience.lower()
        
        # Product-Led Growth is best for many AI tools
        if any(kw in idea_lower for kw in ["developer", "code", "api", "platform"]):
            channels.append("Product-Led Growth (free trial/freemium)")
        
        # Content marketing for complex products
        if any(kw in idea_lower for kw in ["intelligence", "analytics", "platform", "suite"]):
            channels.append("Content Marketing (thought leadership)")
        
        # Paid ads for competitive markets
        if any(kw in idea_lower for kw in ["marketing", "content", "advertising"]):
            channels.append("Paid Advertising (LinkedIn, Google)")
        
        # Outbound for enterprise/high-value
        if any(kw in idea_lower for kw in ["enterprise", "hospital", "law firm", "institution"]) or \
           idea.estimated_mvp_months >= 10:
            channels.append("Outbound Sales (ABM)")
        
        # Partnerships for regulated industries
        if any(kw in idea_lower for kw in ["healthcare", "legal", "finance", "bank"]):
            channels.append("Strategic Partnerships")
        
        # Community for developer tools
        if "developer" in idea_lower or "code" in idea_lower:
            channels.append("Community Building (GitHub, Discord)")
        
        # Default channels
        if not channels:
            channels = ["Content Marketing", "Product-Led Growth", "Strategic Partnerships"]
        
        return channels[:4]  # Return top 4 channels
    
    def _generate_pricing_tiers(self, idea: ProductIdea) -> List[Dict[str, str]]:
        """Generate pricing tier suggestions"""
        pricing_lower = idea.pricing_strategy.lower()
        
        tiers = []
        
        if "free" in pricing_lower or "freemium" in idea.monetization_model.value:
            tiers.append({
                "tier": "Free/Starter",
                "price": "$0 - $49/month",
                "target": "Individual users and small teams",
                "features": "Basic features, limited usage, community support"
            })
        
        if "$" in pricing_lower:
            # Extract price range
            if "$499" in pricing_lower or "$399" in pricing_lower:
                price_range = "$399 - $499/month"
            elif "$199" in pricing_lower:
                price_range = "$199/month"
            elif "$49" in pricing_lower or "$79" in pricing_lower:
                price_range = "$49 - $79/month"
            elif "$1,499" in pricing_lower or "$2,499" in pricing_lower:
                price_range = "$1,499 - $2,499/month"
            else:
                price_range = "$299 - $599/month"
            
            tiers.append({
                "tier": "Professional/Growth",
                "price": price_range,
                "target": "Growing businesses and teams",
                "features": "Full feature set, priority support, higher limits"
            })
        
        if "enterprise" in pricing_lower or "custom" in pricing_lower:
            tiers.append({
                "tier": "Enterprise",
                "price": "Custom pricing",
                "target": "Large organizations with custom needs",
                "features": "Unlimited usage, dedicated support, custom integrations, SLA"
            })
        
        # Default tiers if none generated
        if not tiers:
            tiers = [
                {
                    "tier": "Starter",
                    "price": "$99 - $199/month",
                    "target": "Small teams getting started",
                    "features": "Core features, email support, standard limits"
                },
                {
                    "tier": "Professional",
                    "price": "$499 - $999/month",
                    "target": "Growing organizations",
                    "features": "All features, priority support, advanced analytics"
                },
                {
                    "tier": "Enterprise",
                    "price": "Custom pricing",
                    "target": "Large enterprises",
                    "features": "Unlimited everything, dedicated account manager, custom integrations"
                }
            ]
        
        return tiers
    
    def _develop_marketing_angle(self, idea: ProductIdea) -> str:
        """Develop compelling marketing angle"""
        # Extract key differentiators
        diff = idea.differentiation.lower()
        
        angles = []
        
        # Based on differentiation
        if "accuracy" in diff or "% accuracy" in diff:
            angles.append(f"Industry-leading accuracy with measurable ROI")
        if "explainable" in diff or "white-box" in diff:
            angles.append(f"Transparent AI you can trust with clear explanations")
        if "personalized" in diff or "consistency" in diff:
            angles.append(f"AI that truly understands your unique needs")
        if "autonomous" in diff or "automated" in diff:
            angles.append(f"Reduce manual work by up to 80% with intelligent automation")
        
        # Based on pain point
        problem = idea.primary_pain_point.problem.lower()
        if "time" in problem or "slow" in problem:
            angles.append(f"10x faster than current solutions")
        if "cost" in problem or "expensive" in problem:
            angles.append(f"50% cost reduction compared to traditional approaches")
        if "error" in problem or "accuracy" in problem:
            angles.append(f"Eliminate costly errors and rework")
        
        # Default angle
        if not angles:
            angles.append("Transform your operations with enterprise-grade AI")
        
        return ". ".join(angles[:2]) + "."
    
    def _define_early_adopter(self, idea: ProductIdea) -> str:
        """Define ideal early adopter profile"""
        industry = idea.target_audience.split(",")[0].strip()
        
        profile = f"Early adopter: {industry} teams that are "
        
        profile += "already using AI/ML tools, "
        profile += "feeling pain from current solutions, "
        profile += "have budget for innovation, "
        profile += "willing to be design partners, "
        profile += "can provide feedback and case studies"
        
        return profile
    
    def _identify_partnerships(self, idea: ProductIdea) -> List[str]:
        """Identify strategic partnership opportunities"""
        partnerships = []
        idea_lower = idea.description.lower() + " " + idea.target_audience.lower()
        
        # Tech partnerships based on requirements
        if "github" in idea_lower or "git" in idea_lower:
            partnerships.append("GitHub/GitLab ecosystem partners")
        if "shopify" in idea_lower or "ecommerce" in idea_lower:
            partnerships.append("E-commerce platform partners (Shopify, WooCommerce)")
        if "cms" in idea_lower or "wordpress" in idea_lower:
            partnerships.append("CMS providers and content platform partners")
        if "crm" in idea_lower or "salesforce" in idea_lower or "hubspot" in idea_lower:
            partnerships.append("CRM platform partners (Salesforce, HubSpot)")
        if "zendesk" in idea_lower or "intercom" in idea_lower or "support" in idea_lower:
            partnerships.append("Help desk platform partners")
        if "ats" in idea_lower or "hr" in idea_lower:
            partnerships.append("HRIS and ATS platform partners")
        if "erp" in idea_lower or "supply" in idea_lower:
            partnerships.append("ERP and supply chain system partners")
        
        # Industry partnerships
        if "healthcare" in idea_lower or "medical" in idea_lower:
            partnerships.append("Healthcare system and EMR vendors")
        if "legal" in idea_lower or "law firm" in idea_lower:
            partnerships.append("Legal tech consortiums and bar associations")
        if "finance" in idea_lower or "fintech" in idea_lower or "payment" in idea_lower:
            partnerships.append("Payment processors and fintech infrastructure")
        
        # Default partnerships
        if not partnerships:
            partnerships = [
                "Industry association partnerships",
                "Technology platform integrations",
                "Consulting and implementation partners"
            ]
        
        return partnerships[:4]
    
    def get_channel_priorities(self, channels: List[str]) -> List[Dict[str, str]]:
        """Prioritize channels with timing and budget"""
        prioritized = []
        
        for channel in channels:
            # Match against channel strategies
            for strategy_name, strategy in self.channel_strategies.items():
                if strategy_name.replace("_", " ") in channel.lower() or \
                   strategy_name in channel.lower():
                    prioritized.append({
                        "channel": channel,
                        "time_to_result": strategy["time_to_result"],
                        "cost_level": strategy["cost"],
                        "effectiveness": strategy["effectiveness"],
                        "priority": "High" if strategy["effectiveness"] == "Very high" else "Medium"
                    })
                    break
        
        # Add unknown channels with default values
        for channel in channels:
            if not any(p["channel"] == channel for p in prioritized):
                prioritized.append({
                    "channel": channel,
                    "time_to_result": "3-6 months",
                    "cost_level": "Medium",
                    "effectiveness": "Medium",
                    "priority": "Medium"
                })
        
        return prioritized
    
    def generate_launch_roadmap(self, idea: ProductIdea) -> Dict[str, str]:
        """Generate a launch roadmap timeline"""
        mvp_months = idea.estimated_mvp_months
        
        return {
            f"Month 1-{mvp_months // 3}": "Product development and beta testing with design partners",
            f"Month {mvp_months // 3 + 1}-{mvp_months // 2}": "Alpha release with early adopters, collect feedback",
            f"Month {mvp_months // 2 + 1}-{mvp_months - 1}": "Beta release, refine features, build case studies",
            f"Month {mvp_months}": "Official launch, PR campaign, content marketing push",
            f"Month {mvp_months + 1}-{mvp_months + 3}": "Scale marketing efforts, focus on customer acquisition",
            f"Month {mvp_months + 4}-{mvp_months + 6}": "Enterprise sales push, partnerships, optimize conversion"
        }
