# Usage Examples

This document provides practical examples of using the AI SaaS Market Intelligence Platform.

## Quick Start

### Generate a Full Market Report

```bash
python main.py
```

This outputs:
- Executive summary with key metrics
- Top 5 market opportunities
- Top 8 critical market gaps
- Top 5 product ideas with potential scores

### Get Quick Recommendations

```bash
python main.py recommendations
```

Get the top 5 highest-potential opportunities with:
- Product name and market fit score
- Time to market estimate
- Why now rationale
- First mover targets
- Monetization model and pricing
- Entry strategy

## Deep Dive Examples

### Analyze a Specific Trend

```bash
python main.py analyze "Generative AI for Content Creation"
```

Output includes:
- Trend analysis with growth score and market size
- Related pain points
- 3 top product opportunities
- Competitive landscape with SWOT
- Go-to-market strategies for each product

### Export Data for Further Analysis

```bash
# Export overview
python main.py export market_intelligence.json

# Export recommendations only
python main.js export recommendations.json --format recommendations

# Get JSON output directly
python main.py trends --json > trends.json
```

## Python API Examples

### Example 1: Find Fast-to-Market Opportunities

```python
from ai_saas_intelligence import ProductIdeaGenerator

generator = ProductIdeaGenerator()

# Get ideas that can be built in 6 months or less
fast_ideas = generator.get_ideas_by_mvp_time(6)

print("Fast-to-Market Opportunities (≤6 months):")
for idea in fast_ideas:
    score = generator.score_idea_potential(idea)
    print(f"\n{idea.name} (Score: {score:.0%})")
    print(f"  Target: {idea.target_audience}")
    print(f"  Pricing: {idea.pricing_strategy}")
    print(f"  Differentiation: {idea.differentiation}")
```

### Example 2: Analyze a Specific Industry

```python
from ai_saas_intelligence import PainPointAnalyzer, ProductIdeaGenerator
from ai_saas_intelligence.core.models import MarketSegment

pain_analyzer = PainPointAnalyzer()
idea_gen = ProductIdeaGenerator()

# Get healthcare pain points
healthcare_pain = pain_analyzer.get_pain_points_by_industry(
    MarketSegment.HEALTHCARE
)

print("Healthcare Market Pain Points:")
for pain_point in healthcare_pain:
    print(f"\nSeverity: {pain_point.severity:.0%}")
    print(f"Problem: {pain_point.problem}")
    print(f"Gap: {pain_point.why_insufficient}")
    
    # Generate ideas for this pain point
    ideas = idea_gen.generate_ideas_for_pain_point(pain_point)
    if ideas:
        print(f"Solution Idea: {ideas[0].name}")
```

### Example 3: Competitive Analysis for Entry Strategy

```python
from ai_saas_intelligence import CompetitorAnalyzer

comp_analyzer = CompetitorAnalyzer()

# Analyze content generation market
competitors = comp_analyzer.get_competitors_for_trend(
    "Generative AI for Content Creation"
)

print("Competitive Landscape:")
for comp in competitors:
    print(f"\n{comp.name} ({comp.market_share:.0%} market share)")
    print(f"  Strengths: {', '.join(comp.strengths)}")
    print(f"  Weaknesses: {', '.join(comp.weaknesses)}")
    
    # Analyze competitive gaps
    gap_analysis = comp_analyzer.analyze_competitive_gap(
        "Generative AI for Content Creation", comp
    )
    print(f"  Pricing Gap: {gap_analysis['pricing_gap']}")
    print(f"  Feature Opportunities: {gap_analysis['feature_opportunities']}")

# Get market concentration
concentration = comp_analyzer.get_market_concentration(
    "Generative AI for Content Creation"
)
print(f"\nMarket Concentration: {concentration}")
```

### Example 4: Build Complete GTM Strategy

```python
from ai_saas_intelligence import (
    ProductIdeaGenerator, 
    GTMStrategyGenerator,
    CompetitorAnalyzer
)

idea_gen = ProductIdeaGenerator()
gtm_gen = GTMStrategyGenerator()
comp_analyzer = CompetitorAnalyzer()

# Get a top product idea
ideas = idea_gen.get_top_ideas(1)
idea = ideas[0][0]  # Get the idea object

print(f"Building GTM Strategy for: {idea.name}\n")

# Generate GTM strategy
gtm = gtm_gen.generate_gtm_strategy(idea)

print("Target Segments:")
for segment in gtm.target_segments:
    print(f"  • {segment}")

print("\nAcquisition Channels (Prioritized):")
channels = gtm_gen.get_channel_priorities(gtm.acquisition_channels)
for ch in channels:
    print(f"  • {ch['channel']}")
    print(f"    Priority: {ch['priority']} | Cost: {ch['cost_level']}")
    print(f"    Time to Result: {ch['time_to_result']}")

print("\nPricing Tiers:")
for tier in gtm.pricing_tier_suggestions:
    print(f"  • {tier['tier']}: {tier['price']}")
    print(f"    Target: {tier['target']}")
    print(f"    Features: {tier['features']}")

print(f"\nMarketing Angle: {gtm.marketing_angle}")
print(f"\nEarly Adopter Profile: {gtm.early_adopter_profile}")

print("\nPartnership Opportunities:")
for partnership in gtm.partnership_opportunities:
    print(f"  • {partnership}")

# Get launch roadmap
roadmap = gtm_gen.generate_launch_roadmap(idea)
print("\nLaunch Roadmap:")
for phase, description in roadmap.items():
    print(f"  • {phase}: {description}")
```

### Example 5: Market Opportunity Dashboard

```python
from ai_saas_intelligence import (
    TrendAnalyzer,
    PainPointAnalyzer,
    ProductIdeaGenerator
)
from ai_saas_intelligence.core.orchestrator import MarketIntelligenceOrchestrator

orchestrator = MarketIntelligenceOrchestrator()

# Get comprehensive data
trend_analyzer = TrendAnalyzer()
pain_analyzer = PainPointAnalyzer()
idea_gen = ProductIdeaGenerator()

print("="*70)
print("AI SAAS MARKET INTELLIGENCE DASHBOARD")
print("="*70)

# Top Trends
print("\n📈 TOP MARKET TRENDS")
print("-" * 70)
top_trends = trend_analyzer.get_top_opportunities(5)
for i, trend in enumerate(top_trends, 1):
    print(f"{i}. {trend.name}")
    print(f"   Growth: {trend.growth_potential:.0%} | Market: {trend.market_size_estimate}")
    print(f"   Stage: {trend.adoption_stage}")

# Critical Pain Points
print("\n⚠️  CRITICAL MARKET GAPS")
print("-" * 70)
critical_pain = pain_analyzer.get_high_severity_pain_points(0.88)
for i, pain in enumerate(critical_pain[:5], 1):
    print(f"{i}. [{pain.industry.value.upper()}] {pain.severity:.0%}")
    print(f"   {pain.problem[:80]}...")

# Top Product Ideas
print("\n💡 TOP PRODUCT OPPORTUNITIES")
print("-" * 70)
top_ideas = idea_gen.get_top_ideas(5)
for i, (idea, score) in enumerate(top_ideas, 1):
    print(f"{i}. {idea.name} (Score: {score:.0%})")
    print(f"   Model: {idea.monetization_model.value} | MVP: {idea.estimated_mvp_months}mo")
    print(f"   {idea.differentiation[:80]}...")

# Market Insights
print("\n📊 MARKET INSIGHTS")
print("-" * 70)
overview = orchestrator.generate_overview_report()
print(f"Total Trends Analyzed: {overview['executive_summary']['total_trends_analyzed']}")
print(f"High-Severity Pain Points: {overview['executive_summary']['high_severity_pain_points']}")
print(f"Product Opportunities: {overview['executive_summary']['product_opportunities']}")

# Monetization Model Analysis
models = orchestrator.analyze_monetization_models()
print("\n💰 MONETIZATION MODELS")
print("-" * 70)
for model, examples in models['models'].items():
    print(f"\n{model.upper()}:")
    print(f"  Examples: {', '.join(examples[:3])}")
    if model in models['insights']:
        print(f"  Best For: {models['insights'][model]}")

print("\n" + "="*70)
```

## Use Case Scenarios

### Scenario: Startup Founder Finding Opportunity

**Goal**: Find a fast-to-market, high-potential AI SaaS opportunity

```python
from ai_saas_intelligence import ProductIdeaGenerator, MarketIntelligenceOrchestrator

idea_gen = ProductIdeaGenerator()
orchestrator = MarketIntelligenceOrchestrator()

# Filter for ideas that can be built quickly
fast_ideas = [idea for idea in idea_gen.generate_all_ideas() 
              if idea.estimated_mvp_months <= 7]

# Score and rank
scored = [(idea, idea_gen.score_idea_potential(idea)) 
          for idea in fast_ideas]
scored.sort(key=lambda x: x[1], reverse=True)

print("Top Fast-to-Market Opportunities:")
for idea, score in scored[:3]:
    print(f"\n{idea.name} ({score:.0%} potential)")
    print(f"  Time to Market: {idea.estimated_mvp_months} months")
    print(f"  Monetization: {idea.monetization_model.value}")
    print(f"  Starting Price: {idea.pricing_strategy.split(',')[0]}")
    
    # Get GTM strategy
    gtm = orchestrator.gtm_generator.generate_gtm_strategy(idea)
    print(f"  First Channel: {gtm.acquisition_channels[0]}")
    print(f"  First Target: {gtm.target_segments[0]}")
```

### Scenario: Enterprise Team Evaluating Market Entry

**Goal**: Comprehensive analysis before entering a new market

```python
from ai_saas_intelligence import (
    TrendAnalyzer,
    CompetitorAnalyzer,
    MarketIntelligenceOrchestrator
)

orchestrator = MarketIntelligenceOrchestrator()
trend_analyzer = TrendAnalyzer()
comp_analyzer = CompetitorAnalyzer()

# Analyze AI Marketing Automation market
trend_name = "AI Marketing Automation & Attribution"

# Get trend analysis
trend_analysis = trend_analyzer.analyze_trend_potential(trend_name)
print(f"Growth Potential: {trend_analysis['growth_score']:.0%}")
print(f"Opportunity Level: {trend_analysis['opportunity_level']}")

# Competitive landscape
competitors = comp_analyzer.get_competitors_for_trend(trend_name)
print(f"\nCompetitors: {len(competitors)}")

swot = comp_analyzer.get_swot_summary(trend_name)
print("\nMarket Threats:")
for threat in swot.get('Market_Threats', [])[:3]:
    print(f"  • {threat}")

print("\nMarket Opportunities:")
for opp in swot.get('Market_Opportunities', [])[:3]:
    print(f"  • {opp}")

# Market concentration
concentration = comp_analyzer.get_market_concentration(trend_name)
print(f"\nMarket Concentration: {concentration}")

# Get full report
report = orchestrator._generate_trend_report(trend_name)
print(f"\nProduct Opportunities: {len(report['product_ideas'])}")
```

### Scenario: Investor Pitch Preparation

**Goal**: Gather data for investor presentation

```python
from ai_saas_intelligence import MarketIntelligenceOrchestrator

orchestrator = MarketIntelligenceOrchestrator()

# Get market size and growth data
overview = orchestrator.generate_overview_report()

print("MARKET OPPORTUNITY")
print("="*50)

# Top opportunity
top_opp = overview['top_market_opportunities'][0]
print(f"\nTrend: {top_opp['trend']}")
print(f"Market Size: {top_opp['market_size']}")
print(f"Growth Rate: {top_opp['growth_potential']}")
print(f"Key Tech: {', '.join(top_opp['key_tech'])}")

# Problem-Solution fit
gap = overview['critical_market_gaps'][0]
print(f"\nPROBLEM:")
print(f"  {gap['problem']}")
print(f"  Severity: {gap['severity']}")

solution = overview['top_product_ideas'][0]
print(f"\nSOLUTION:")
print(f"  {solution['name']}")
print(f"  {solution['description']}")
print(f"  Monetization: {solution['monetization']}")

# Competitive advantage
print(f"\nCOMPETITIVE ADVANTAGE:")
print(f"  {solution['differentiation']}")

# Go-to-market
print(f"\nGO-TO-MARKET:")
print(f"  Target: {solution['target_audience']}")
print(f"  Pricing: {solution['pricing']}")
print(f"  Time to Market: {solution['mvp_months']} months")
```

## Tips for Effective Use

1. **Start with recommendations**: Use `python main.py recommendations` for quick insights
2. **Deep dive on trends**: Use `analyze` command for comprehensive market analysis
3. **Export for analysis**: Use JSON export for custom analysis in tools like Excel or Tableau
4. **Combine data sources**: Use Python API to combine platform data with your own research
5. **Validate externally**: Platform data should be validated with additional market research

## Integration Examples

### Export to CSV (using pandas)

```python
import pandas as pd
from ai_saas_intelligence import ProductIdeaGenerator

gen = ProductIdeaGenerator()
ideas = gen.generate_all_ideas()

data = [{
    'Name': idea.name,
    'Description': idea.description,
    'Target': idea.target_audience,
    'Monetization': idea.monetization_model.value,
    'Pricing': idea.pricing_strategy,
    'MVP_Months': idea.estimated_mvp_months,
    'Differentiation': idea.differentiation,
    'Score': gen.score_idea_potential(idea)
} for idea in ideas]

df = pd.DataFrame(data)
df.to_csv('product_opportunities.csv', index=False)
print("Exported to product_opportunities.csv")
```

### Web API Integration (FastAPI example)

```python
from fastapi import FastAPI
from ai_saas_intelligence import MarketIntelligenceOrchestrator

app = FastAPI()
orchestrator = MarketIntelligenceOrchestrator()

@app.get("/api/opportunities")
async def get_opportunities(count: int = 5):
    """Get top market opportunities"""
    return {"opportunities": orchestrator.get_quick_recommendations(count)}

@app.get("/api/trends")
async def get_trends():
    """Get all market trends"""
    from ai_saas_intelligence import TrendAnalyzer
    ta = TrendAnalyzer()
    return {
        "trends": [
            {
                "name": t.name,
                "growth": t.growth_potential,
                "market_size": t.market_size_estimate
            }
            for t in ta.get_all_trends()
        ]
    }

@app.get("/api/analyze/{trend}")
async def analyze_trend(trend: str):
    """Analyze specific trend"""
    return orchestrator._generate_trend_report(trend)
```
