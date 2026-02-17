"""Tests for TrendAnalyzer"""

import pytest
from ai_saas_intelligence.analyzers.trend_analyzer import TrendAnalyzer
from ai_saas_intelligence.core.models import MarketSegment


class TestTrendAnalyzer:
    
    def setup_method(self):
        """Setup test fixtures"""
        self.analyzer = TrendAnalyzer()
    
    def test_get_all_trends(self):
        """Test retrieving all trends"""
        trends = self.analyzer.get_all_trends()
        
        assert len(trends) > 0
        assert all(hasattr(t, 'name') for t in trends)
        assert all(hasattr(t, 'growth_potential') for t in trends)
        assert all(0 <= t.growth_potential <= 1 for t in trends)
    
    def test_get_trends_by_growth_potential(self):
        """Test filtering trends by growth potential"""
        high_growth = self.analyzer.get_trends_by_growth_potential(0.8)
        
        assert all(t.growth_potential >= 0.8 for t in high_growth)
        
        very_high = self.analyzer.get_trends_by_growth_potential(0.9)
        assert len(very_high) <= len(high_growth)
    
    def test_get_trends_by_adoption_stage(self):
        """Test filtering trends by adoption stage"""
        growing_trends = self.analyzer.get_trends_by_adoption_stage("growing")
        
        assert all(t.adoption_stage == "growing" for t in growing_trends)
        assert len(growing_trends) > 0
    
    def test_get_trends_by_technology(self):
        """Test filtering trends by technology"""
        llm_trends = self.analyzer.get_trends_by_technology("LLM")
        
        assert len(llm_trends) > 0
        assert any("LLM" in t.key_technologies for t in llm_trends)
    
    def test_get_top_opportunities(self):
        """Test getting top opportunities"""
        top_3 = self.analyzer.get_top_opportunities(3)
        top_5 = self.analyzer.get_top_opportunities(5)
        
        assert len(top_3) == 3
        assert len(top_5) == 5
        
        # Verify sorted by growth potential
        assert top_3[0].growth_potential >= top_3[1].growth_potential
        assert top_3[1].growth_potential >= top_3[2].growth_potential
    
    def test_analyze_trend_potential(self):
        """Test deep trend analysis"""
        # Test with a known trend
        trends = self.analyzer.get_all_trends()
        if trends:
            analysis = self.analyzer.analyze_trend_potential(trends[0].name)
            
            assert 'name' in analysis
            assert 'growth_score' in analysis
            assert 'growth_rating' in analysis
            assert 'market_size' in analysis
            assert 'opportunity_level' in analysis
    
    def test_analyze_trend_potential_invalid(self):
        """Test trend analysis with invalid trend name"""
        with pytest.raises(ValueError):
            self.analyzer.analyze_trend_potential("Non-existent Trend")
    
    def test_get_growth_rating(self):
        """Test growth rating conversion"""
        assert self.analyzer._get_growth_rating(0.95) == "Exceptional"
        assert self.analyzer._get_growth_rating(0.85) == "High"
        assert self.analyzer._get_growth_rating(0.75) == "Moderate"
        assert self.analyzer._get_growth_rating(0.5) == "Low"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
