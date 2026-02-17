"""Tests for ProductIdeaGenerator"""

import pytest
from ai_saas_intelligence.generators.product_idea_generator import ProductIdeaGenerator
from ai_saas_intelligence.core.models import PainPoint, MarketSegment, MonetizationModel


class TestProductIdeaGenerator:
    
    def setup_method(self):
        """Setup test fixtures"""
        self.generator = ProductIdeaGenerator()
    
    def test_generate_all_ideas(self):
        """Test generating all product ideas"""
        ideas = self.generator.generate_all_ideas()
        
        assert len(ideas) > 0
        assert all(hasattr(idea, 'name') for idea in ideas)
        assert all(hasattr(idea, 'description') for idea in ideas)
        assert all(hasattr(idea, 'monetization_model') for idea in ideas)
        assert all(hasattr(idea, 'estimated_mvp_months') for idea in ideas)
        assert all(idea.estimated_mvp_months > 0 for idea in ideas)
    
    def test_generate_ideas_for_pain_point(self):
        """Test generating ideas for specific pain point"""
        pain_point = PainPoint(
            industry=MarketSegment.FINANCE,
            problem="Fraud detection challenges",
            severity=0.90,
            current_solutions=["Rule-based systems"],
            why_insufficient="High false positives"
        )
        
        ideas = self.generator.generate_ideas_for_pain_point(pain_point)
        
        assert len(ideas) > 0
        assert all(idea.primary_pain_point == pain_point for idea in ideas)
    
    def test_get_ideas_by_monetization_model(self):
        """Test filtering ideas by monetization model"""
        subscription_ideas = self.generator.get_ideas_by_monetization_model(
            MonetizationModel.SUBSCRIPTION
        )
        
        assert all(idea.monetization_model == MonetizationModel.SUBSCRIPTION 
                   for idea in subscription_ideas)
    
    def test_get_ideas_by_mvp_time(self):
        """Test filtering ideas by MVP timeline"""
        fast_ideas = self.generator.get_ideas_by_mvp_time(6)
        slow_ideas = self.generator.get_ideas_by_mvp_time(12)
        
        assert all(idea.estimated_mvp_months <= 6 for idea in fast_ideas)
        assert all(idea.estimated_mvp_months <= 12 for idea in slow_ideas)
        assert len(slow_ideas) >= len(fast_ideas)
    
    def test_score_idea_potential(self):
        """Test idea potential scoring"""
        ideas = self.generator.generate_all_ideas()
        
        for idea in ideas:
            score = self.generator.score_idea_potential(idea)
            assert 0 <= score <= 1
    
    def test_get_top_ideas(self):
        """Test getting top ideas by potential"""
        top_3 = self.generator.get_top_ideas(3)
        top_5 = self.generator.get_top_ideas(5)
        
        assert len(top_3) == 3
        assert len(top_5) == 5
        
        # Verify sorted by score
        assert top_3[0][1] >= top_3[1][1] >= top_3[2][1]
        
        # Verify scores are valid
        assert all(0 <= score <= 1 for _, score in top_5)
    
    def test_idea_templates_structure(self):
        """Test idea templates have required fields"""
        templates = self.generator.idea_templates
        
        required_fields = [
            'pain_point_keywords', 'product_name', 'description',
            'target_audience', 'monetization_model', 'pricing_strategy',
            'key_features', 'technical_requirements', 'differentiation',
            'estimated_mvp_months'
        ]
        
        for template in templates:
            for field in required_fields:
                assert field in template


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
