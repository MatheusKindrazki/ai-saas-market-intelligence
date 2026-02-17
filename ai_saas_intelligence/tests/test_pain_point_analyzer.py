"""Tests for PainPointAnalyzer"""

import pytest
from ai_saas_intelligence.analyzers.pain_point_analyzer import PainPointAnalyzer
from ai_saas_intelligence.core.models import MarketSegment


class TestPainPointAnalyzer:
    
    def setup_method(self):
        """Setup test fixtures"""
        self.analyzer = PainPointAnalyzer()
    
    def test_get_all_pain_points(self):
        """Test retrieving pain points database"""
        pain_points = self.analyzer.pain_points_db
        
        assert len(pain_points) > 0
        assert all(hasattr(p, 'industry') for p in pain_points)
        assert all(hasattr(p, 'problem') for p in pain_points)
        assert all(hasattr(p, 'severity') for p in pain_points)
        assert all(0 <= p.severity <= 1 for p in pain_points)
    
    def test_get_pain_points_by_industry(self):
        """Test filtering pain points by industry"""
        healthcare_pain = self.analyzer.get_pain_points_by_industry(MarketSegment.HEALTHCARE)
        
        assert len(healthcare_pain) > 0
        assert all(p.industry == MarketSegment.HEALTHCARE for p in healthcare_pain)
        
        finance_pain = self.analyzer.get_pain_points_by_industry(MarketSegment.FINANCE)
        assert all(p.industry == MarketSegment.FINANCE for p in finance_pain)
    
    def test_get_high_severity_pain_points(self):
        """Test filtering by severity threshold"""
        high_severity = self.analyzer.get_high_severity_pain_points(0.8)
        very_high = self.analyzer.get_high_severity_pain_points(0.9)
        
        assert all(p.severity >= 0.8 for p in high_severity)
        assert all(p.severity >= 0.9 for p in very_high)
        assert len(very_high) <= len(high_severity)
    
    def test_get_opportunity_gaps(self):
        """Test opportunity gap identification"""
        gaps = self.analyzer.get_opportunity_gaps()
        
        assert len(gaps) > 0
        assert all('industry' in gap for gap in gaps)
        assert all('problem' in gap for gap in gaps)
        assert all('severity_score' in gap for gap in gaps)
        assert all('opportunity_rating' in gap for gap in gaps)
        
        # Verify sorted by severity
        assert gaps[0]['severity_score'] >= gaps[-1]['severity_score']
    
    def test_find_pain_points_by_keyword(self):
        """Test keyword search in pain points"""
        fraud_results = self.analyzer.find_pain_points_by_keyword("fraud")
        
        assert len(fraud_results) > 0
        assert any("fraud" in p.problem.lower() for p in fraud_results)
    
    def test_get_top_n_pain_points(self):
        """Test getting top N pain points"""
        top_5 = self.analyzer.get_top_n_pain_points(5)
        top_10 = self.analyzer.get_top_n_pain_points(10)
        
        assert len(top_5) == 5
        assert len(top_10) == 10
        
        # Verify sorted by severity
        assert top_5[0].severity >= top_5[4].severity
    
    def test_rate_opportunity(self):
        """Test opportunity rating"""
        from ai_saas_intelligence.core.models import PainPoint
        
        critical = PainPoint(
            industry=MarketSegment.HEALTHCARE,
            problem="Test problem",
            severity=0.90,
            current_solutions=[],
            why_insufficient="Test"
        )
        rating = self.analyzer._rate_opportunity(critical)
        assert rating == "Critical Opportunity"
        
        high = PainPoint(
            industry=MarketSegment.MARKETING,
            problem="Test problem 2",
            severity=0.85,
            current_solutions=[],
            why_insufficient="Test"
        )
        rating = self.analyzer._rate_opportunity(high)
        assert rating == "High Priority"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
