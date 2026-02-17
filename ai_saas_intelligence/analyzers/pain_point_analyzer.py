"""Pain point and gap analyzer for identifying market opportunities"""

from typing import List
from ..core.models import PainPoint, MarketSegment


class PainPointAnalyzer:
    """Identifies and analyzes pain points across different market segments"""
    
    def __init__(self):
        self.pain_points_db = self._initialize_pain_points_database()
    
    def _initialize_pain_points_database(self) -> List[PainPoint]:
        """Initialize comprehensive pain points database"""
        return [
            # Healthcare
            PainPoint(
                industry=MarketSegment.HEALTHCARE,
                problem="Manual medical imaging analysis is time-consuming and prone to human error",
                severity=0.88,
                current_solutions=["Radiologist review", "Legacy CAD systems"],
                why_insufficient="Specialist shortage, long turnaround times, variable accuracy rates"
            ),
            PainPoint(
                industry=MarketSegment.HEALTHCARE,
                problem="Patient data is siloed across incompatible systems, hindering holistic care",
                severity=0.85,
                current_solutions=["EMR/EHR systems", "Manual data entry"],
                why_insufficient="Poor interoperability, manual data transfer errors, incomplete patient histories"
            ),
            
            # Finance
            PainPoint(
                industry=MarketSegment.FINANCE,
                problem="Real-time fraud detection struggles with sophisticated, evolving attack patterns",
                severity=0.90,
                current_solutions=["Rule-based systems", "Basic ML models"],
                why_insufficient="High false positives, inability to adapt quickly, expensive manual review"
            ),
            PainPoint(
                industry=MarketSegment.FINANCE,
                problem="Credit risk assessment relies on limited data sources and manual processes",
                severity=0.82,
                current_solutions=["FICO scores", "Manual underwriting"],
                why_insufficient="Limited visibility into alternative data, slow approval processes, bias concerns"
            ),
            
            # E-commerce
            PainPoint(
                industry=MarketSegment.E_COMMERCE,
                problem="High customer acquisition costs and low retention rates plague online retailers",
                severity=0.86,
                current_solutions=["Discount campaigns", "Basic email marketing"],
                why_insufficient="Generic personalization, poor timing, inability to predict churn accurately"
            ),
            PainPoint(
                industry=MarketSegment.E_COMMERCE,
                problem="Product descriptions and marketing copy creation is labor-intensive and inconsistent",
                severity=0.75,
                current_solutions=["Manual copywriting", "Template generators"],
                why_insufficient="Slow production, quality inconsistency, poor SEO optimization"
            ),
            
            # Education
            PainPoint(
                industry=MarketSegment.EDUCATION,
                problem="One-size-fits-all education fails to address individual learning gaps and styles",
                severity=0.84,
                current_solutions=["Standard curriculum", "Tutoring"],
                why_insufficient="Expensive, not scalable, lacks real-time feedback and personalization"
            ),
            PainPoint(
                industry=MarketSegment.EDUCATION,
                problem="Teachers spend excessive time on grading and administrative tasks",
                severity=0.78,
                current_solutions=["Manual grading", "LMS basic automation"],
                why_insufficient="Time-consuming, subjective grading, limited feedback quality"
            ),
            
            # Legal
            PainPoint(
                industry=MarketSegment.LEGAL,
                problem="Contract review is expensive, slow, and requires specialized expertise",
                severity=0.85,
                current_solutions=["Manual review", "Basic keyword search"],
                why_insufficient="High hourly rates, slow turnaround, risk of missing critical clauses"
            ),
            PainPoint(
                industry=MarketSegment.LEGAL,
                problem="Legal research is time-intensive with vast document repositories to navigate",
                severity=0.80,
                current_solutions=["LexisNexis", "Westlaw"],
                why_insufficient="Expensive subscriptions, complex queries, difficult to find precedents quickly"
            ),
            
            # Marketing
            PainPoint(
                industry=MarketSegment.MARKETING,
                problem="Marketing ROI attribution is fragmented and difficult to measure accurately",
                severity=0.82,
                current_solutions=["GA4", "Marketing attribution tools"],
                why_insufficient="Data silos, cross-channel challenges, delayed insights"
            ),
            PainPoint(
                industry=MarketSegment.MARKETING,
                problem="Content creation at scale is resource-intensive and quality varies",
                severity=0.87,
                current_solutions=["Content teams", "Freelance writers"],
                why_insufficient="High costs, production bottlenecks, inconsistent brand voice"
            ),
            
            # HR
            PainPoint(
                industry=MarketSegment.HR,
                problem="Hiring is inefficient with poor candidate matching and long time-to-fill",
                severity=0.83,
                current_solutions=["LinkedIn", "ATS systems"],
                why_insufficient="Resume spam, poor matching algorithms, manual screening burden"
            ),
            PainPoint(
                industry=MarketSegment.HR,
                problem="Employee turnover prediction and prevention is reactive rather than proactive",
                severity=0.76,
                current_solutions=["Exit interviews", "Surveys"],
                why_insufficient="Too late, self-reported bias, limited predictive power"
            ),
            
            # Development
            PainPoint(
                industry=MarketSegment.DEVELOPMENT,
                problem="Code review is a bottleneck and quality varies by reviewer expertise",
                severity=0.84,
                current_solutions=["Manual PR reviews", "Basic linters"],
                why_insufficient="Time-consuming, inconsistent standards, reviewer fatigue"
            ),
            PainPoint(
                industry=MarketSegment.DEVELOPMENT,
                problem="Testing coverage is often incomplete and test maintenance is costly",
                severity=0.79,
                current_solutions=["Unit tests", "Manual QA"],
                why_insufficient="Flaky tests, limited edge case coverage, high maintenance overhead"
            ),
            
            # Operations
            PainPoint(
                industry=MarketSegment.OPERATIONS,
                problem="Supply chain disruptions are hard to predict and respond to quickly",
                severity=0.86,
                current_solutions=["ERP systems", "Spreadsheets"],
                why_insufficient="Reactive not predictive, slow response, limited visibility"
            ),
            PainPoint(
                industry=MarketSegment.OPERATIONS,
                problem="Inventory management is inefficient with overstock and stockouts common",
                severity=0.78,
                current_solutions=["Basic forecasting", "Min-max policies"],
                why_insufficient="Inaccurate demand prediction, static policies, waste costs"
            ),
            
            # Customer Service
            PainPoint(
                industry=MarketSegment.CUSTOMER_SERVICE,
                problem="Support ticket volume overwhelms teams, leading to poor response times",
                severity=0.88,
                current_solutions=["IVR", "Basic chatbots"],
                why_insufficient="Frustrating experiences, limited resolution, escalations still high"
            ),
            PainPoint(
                industry=MarketSegment.CUSTOMER_SERVICE,
                problem="Customer sentiment analysis is reactive and misses early warning signs",
                severity=0.75,
                current_solutions=["Surveys", "Keyword monitoring"],
                why_insufficient="Low response rates, delayed feedback, limited context"
            )
        ]
    
    def get_pain_points_by_industry(self, industry: MarketSegment) -> List[PainPoint]:
        """Get pain points for a specific industry"""
        return [p for p in self.pain_points_db if p.industry == industry]
    
    def get_high_severity_pain_points(self, min_severity: float = 0.8) -> List[PainPoint]:
        """Get pain points above severity threshold"""
        return [p for p in self.pain_points_db if p.severity >= min_severity]
    
    def get_opportunity_gaps(self) -> List[dict]:
        """Identify gaps where current solutions are most insufficient"""
        gaps = []
        for pain_point in self.pain_points_db:
            if pain_point.severity >= 0.8:
                gaps.append({
                    "industry": pain_point.industry.value,
                    "problem": pain_point.problem,
                    "severity_score": pain_point.severity,
                    "gap_description": pain_point.why_insufficient,
                    "opportunity_rating": self._rate_opportunity(pain_point)
                })
        return sorted(gaps, key=lambda x: x["severity_score"], reverse=True)

    def rate_opportunity(self, pain_point: PainPoint) -> str:
        """Rate the opportunity level based on severity and solution gaps (public API)"""
        return self._rate_opportunity(pain_point)

    def _rate_opportunity(self, pain_point: PainPoint) -> str:
        """Rate the opportunity level based on severity and solution gaps"""
        if pain_point.severity >= 0.88:
            return "Critical Opportunity"
        elif pain_point.severity >= 0.82:
            return "High Priority"
        elif pain_point.severity >= 0.75:
            return "Moderate Opportunity"
        else:
            return "Watch"
    
    def find_pain_points_by_keyword(self, keyword: str) -> List[PainPoint]:
        """Find pain points containing specific keywords"""
        keyword_lower = keyword.lower()
        return [
            p for p in self.pain_points_db
            if keyword_lower in p.problem.lower() or keyword_lower in p.why_insufficient.lower()
        ]
    
    def get_top_n_pain_points(self, count: int = 10) -> List[PainPoint]:
        """Get top N pain points by severity"""
        return sorted(self.pain_points_db, key=lambda x: x.severity, reverse=True)[:count]
