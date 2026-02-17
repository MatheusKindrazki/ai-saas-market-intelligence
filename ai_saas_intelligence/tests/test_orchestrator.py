"""Tests for MarketIntelligenceOrchestrator"""

import pytest
from ai_saas_intelligence.core.orchestrator import MarketIntelligenceOrchestrator


class TestMarketIntelligenceOrchestrator:
    
    def setup_method(self):
        """Setup test fixtures"""
        self.orchestrator = MarketIntelligenceOrchestrator()
    
    def test_initialization(self):
        """Test orchestrator initialization"""
        assert self.orchestrator.trend_analyzer is not None
        assert self.orchestrator.pain_point_analyzer is not None
        assert self.orchestrator.competitor_analyzer is not None
        assert self.orchestrator.idea_generator is not None
        assert self.orchestrator.gtm_generator is not None
    
    def test_generate_overview_report(self):
        """Test overview report generation"""
        report = self.orchestrator._generate_overview_report()
        
        assert 'executive_summary' in report
        assert 'top_market_opportunities' in report
        assert 'critical_market_gaps' in report
        assert 'top_product_ideas' in report
        
        assert len(report['top_market_opportunities']) > 0
        assert len(report['critical_market_gaps']) > 0
        assert len(report['top_product_ideas']) > 0
    
    def test_generate_trend_report(self):
        """Test detailed trend report generation"""
        # Get a valid trend name
        trends = self.orchestrator.trend_analyzer.get_all_trends()
        if trends:
            report = self.orchestrator._generate_trend_report(trends[0].name)
            
            assert 'trend_analysis' in report
            assert 'pain_points' in report
            assert 'product_ideas' in report
            assert 'competitive_landscape' in report
            assert 'go_to_market' in report
    
    def test_get_quick_recommendations(self):
        """Test quick recommendations generation"""
        recommendations = self.orchestrator.get_quick_recommendations(3)
        
        assert len(recommendations) > 0
        assert len(recommendations) <= 3
        
        for rec in recommendations:
            assert 'product' in rec
            assert 'market_fit' in rec
            assert 'time_to_market' in rec
            assert 'monetization' in rec
    
    def test_analyze_monetization_models(self):
        """Test monetization model analysis"""
        analysis = self.orchestrator.analyze_monetization_models()
        
        assert 'models' in analysis
        assert 'insights' in analysis
        
        assert len(analysis['models']) > 0
        assert len(analysis['insights']) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
