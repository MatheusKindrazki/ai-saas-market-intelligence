#!/usr/bin/env python3
"""AI SaaS Market Intelligence CLI - Actionable market analysis for AI SaaS opportunities"""

import sys
import json
import argparse
from pathlib import Path

# Add the project to the path
sys.path.insert(0, str(Path(__file__).parent))

from ai_saas_intelligence import (
    TrendAnalyzer,
    PainPointAnalyzer,
    CompetitorAnalyzer,
    ProductIdeaGenerator,
    GTMStrategyGenerator
)
from ai_saas_intelligence.core.orchestrator import MarketIntelligenceOrchestrator


def format_json_output(data: dict, indent: int = 2) -> str:
    """Format data as JSON string"""
    return json.dumps(data, indent=indent, ensure_ascii=False)


def print_section(title: str, content: str = ""):
    """Print a formatted section"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
    if content:
        print(content)


def print_overview_report():
    """Generate and display overview report"""
    orchestrator = MarketIntelligenceOrchestrator()
    report = orchestrator.generate_overview_report()
    
    print_section("AI SaaS MARKET INTELLIGENCE REPORT")
    print(f"\nGenerated comprehensive analysis of {report['executive_summary']['total_trends_analyzed']} market trends, "
          f"{report['executive_summary']['high_severity_pain_points']} critical pain points, "
          f"and {report['executive_summary']['product_opportunities']} product opportunities.\n")
    
    # Top Opportunities
    print_section("TOP MARKET OPPORTUNITIES")
    for i, opp in enumerate(report['top_market_opportunities'], 1):
        print(f"\n{i}. {opp['trend']}")
        print(f"   Growth Potential: {opp['growth_potential']}")
        print(f"   Market Size: {opp['market_size']}")
        print(f"   Adoption Stage: {opp['adoption_stage']}")
        print(f"   Key Technologies: {', '.join(opp['key_tech'])}")
    
    # Critical Market Gaps
    print_section("CRITICAL MARKET GAPS (By Severity)")
    for i, gap in enumerate(report['critical_market_gaps'], 1):
        print(f"\n{i}. [{gap['industry'].upper()}] {gap['opportunity_rating']}")
        print(f"   Problem: {gap['problem']}")
        print(f"   Severity: {gap['severity']}")
    
    # Top Product Ideas
    print_section("TOP PRODUCT IDEAS (By Potential Score)")
    for i, idea in enumerate(report['top_product_ideas'], 1):
        print(f"\n{i}. {idea['name']} - Score: {idea['potential_score']}")
        print(f"   Description: {idea['description']}")
        print(f"   Target: {idea['target_audience']}")
        print(f"   Monetization: {idea['monetization']}")
        print(f"   Pricing: {idea['pricing']}")
        print(f"   MVP Timeline: {idea['mvp_months']} months")
        print(f"   Differentiation: {idea['key_differentiators']}")
    
    print_section("END OF REPORT")


def print_trend_report(trend_name: str):
    """Generate and display detailed trend report"""
    orchestrator = MarketIntelligenceOrchestrator()
    report = orchestrator.generate_comprehensive_report(trend_name)
    
    print_section(f"DETAILED ANALYSIS: {trend_name.upper()}")
    
    # Trend Analysis
    ta = report['trend_analysis']
    print(f"\n{ta['name']}")
    print(f"Growth Score: {ta['growth_score']:.0%} ({ta['growth_rating']})")
    print(f"Market Size: {ta['market_size']}")
    print(f"Adoption Stage: {ta['adoption_stage']}")
    print(f"Opportunity Level: {ta['opportunity_level']}")
    print(f"Key Differentiators: {', '.join(ta['key_differentiators'])}")
    
    # Pain Points
    print_section("RELATED PAIN POINTS")
    for i, pp in enumerate(report['pain_points'], 1):
        print(f"\n{i}. [{pp['industry'].upper()}] Severity: {pp['severity']}")
        print(f"   Problem: {pp['problem']}")
        print(f"   Gap: {pp['gap']}")
    
    # Product Ideas
    print_section("PRODUCT OPPORTUNITIES")
    for i, idea in enumerate(report['product_ideas'], 1):
        print(f"\n{i}. {idea['name']} - Score: {idea['potential_score']}")
        print(f"   Description: {idea['description']}")
        print(f"   Target: {idea['target_audience']}")
        print(f"   Monetization: {idea['monetization']}")
        print(f"   Pricing: {idea['pricing']}")
        print(f"   MVP: {idea['mvp_months']} months")
        print(f"   Differentiation: {idea['differentiation']}")
    
    # Competitive Landscape
    cl = report['competitive_landscape']
    print_section(f"COMPETITIVE LANDSCAPE - {cl['market_concentration']}")
    
    if cl['competitors']:
        print("\nKey Competitors:")
        for comp in cl['competitors']:
            print(f"\n  {comp['name']} ({comp['market_share']})")
            print(f"  Strengths: {', '.join(comp['strengths'])}")
            print(f"  Weaknesses: {', '.join(comp['weaknesses'])}")
            print(f"  Pricing: {comp['pricing']}")
    
    swot = cl['swot_summary']
    print("\nSWOT Summary:")
    print(f"  Market Threats: {', '.join(swot.get('Market_Threats', [])[:3])}")
    print(f"  Market Opportunities: {', '.join(swot.get('Market_Opportunities', [])[:3])}")
    
    # GTM Strategies
    print_section("GO-TO-MARKET STRATEGIES")
    for gtm in report['go_to_market']:
        print(f"\nProduct: {gtm['idea_name']}")
        print(f"Target Segments: {', '.join(gtm['target_segments'])}")
        print(f"Channels: {', '.join(gtm['acquisition_channels'])}")
        print(f"Marketing Angle: {gtm['marketing_angle']}")
        print(f"Early Adopter: {gtm['early_adopter']}")
        print(f"Partnerships: {', '.join(gtm['partnership_opportunities'])}")
        print(f"\nPricing Tiers:")
        for tier in gtm['pricing_tiers']:
            print(f"  • {tier['tier']}: {tier['price']}")
            print(f"    Target: {tier['target']}")
    
    print_section("END OF REPORT")


def print_quick_recommendations():
    """Print quick recommendations"""
    orchestrator = MarketIntelligenceOrchestrator()
    recommendations = orchestrator.get_quick_recommendations(5)
    
    print_section("QUICK RECOMMENDATIONS - TOP 5 OPPORTUNITIES")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['product']}")
        print(f"   Market Fit: {rec['market_fit']}")
        print(f"   Time to Market: {rec['time_to_market']}")
        print(f"   Why Now: {rec['why_now']}")
        print(f"   First Movers: {rec['first_movers']}")
        print(f"   Monetization: {rec['monetization']}")
        print(f"   Starting Price: {rec['starting_price']}")
        print(f"   Entry Strategy: {rec['entry_strategy']}")
    
    print_section("END OF RECOMMENDATIONS")


def list_trends():
    """List all market trends"""
    analyzer = TrendAnalyzer()
    trends = analyzer.get_all_trends()
    
    print_section("MARKET TRENDS")
    for i, trend in enumerate(trends, 1):
        print(f"\n{i}. {trend.name}")
        print(f"   Growth: {trend.growth_potential:.0%} | Size: {trend.market_size_estimate}")
        print(f"   Stage: {trend.adoption_stage}")
        print(f"   Tech: {', '.join(trend.key_technologies)}")


def list_pain_points():
    """List all pain points"""
    analyzer = PainPointAnalyzer()
    pain_points = analyzer.get_top_n_pain_points(20)
    
    print_section("MARKET PAIN POINTS")
    for i, pp in enumerate(pain_points, 1):
        print(f"\n{i}. [{pp.industry.value.upper()}] Severity: {pp.severity:.0%}")
        print(f"   Problem: {pp.problem}")


def list_ideas():
    """List all product ideas"""
    generator = ProductIdeaGenerator()
    ideas = generator.generate_all_ideas()
    
    print_section("PRODUCT IDEAS")
    for i, idea in enumerate(ideas, 1):
        score = generator.score_idea_potential(idea)
        print(f"\n{i}. {idea.name} (Score: {score:.0%})")
        print(f"   Target: {idea.target_audience}")
        print(f"   Monetization: {idea.monetization_model.value}")
        print(f"   MVP: {idea.estimated_mvp_months} months")


def export_report(output_file: str, report_format: str = "overview"):
    """Export report to file"""
    orchestrator = MarketIntelligenceOrchestrator()

    if report_format == "overview":
        report = orchestrator.generate_overview_report()
    elif report_format == "recommendations":
        report = {"recommendations": orchestrator.get_quick_recommendations(10)}
    else:
        # Default to overview
        report = orchestrator.generate_overview_report()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"Report exported to: {output_file}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="AI SaaS Market Intelligence Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Show overview report
  python main.py trends             # List all market trends
  python main.py pain-points        # List all pain points
  python main.py ideas              # List all product ideas
  python main.py analyze "Generative AI for Content Creation"  # Detailed trend analysis
  python main.py recommendations     # Quick recommendations
  python main.py export report.json # Export report to file
        """
    )
    
    parser.add_argument(
        'command',
        nargs='?',
        choices=['trends', 'pain-points', 'ideas', 'recommendations', 'analyze', 'export'],
        help='Command to execute'
    )
    
    parser.add_argument(
        'argument',
        nargs='?',
        help='Argument for command (e.g., trend name for analyze, file path for export)'
    )
    
    parser.add_argument(
        '--format',
        choices=['overview', 'recommendations', 'full'],
        default='overview',
        help='Report format for export command'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )
    
    args = parser.parse_args()
    
    # Execute command
    if args.command is None or args.command == 'overview':
        if args.json:
            orchestrator = MarketIntelligenceOrchestrator()
            print(format_json_output(orchestrator.generate_overview_report()))
        else:
            print_overview_report()
    
    elif args.command == 'trends':
        if args.json:
            analyzer = TrendAnalyzer()
            trends = [
                {
                    "name": t.name,
                    "growth_potential": t.growth_potential,
                    "market_size": t.market_size_estimate,
                    "adoption_stage": t.adoption_stage,
                    "key_technologies": t.key_technologies
                }
                for t in analyzer.get_all_trends()
            ]
            print(format_json_output(trends))
        else:
            list_trends()
    
    elif args.command == 'pain-points':
        if args.json:
            analyzer = PainPointAnalyzer()
            pain_points = [
                {
                    "industry": p.industry.value,
                    "problem": p.problem,
                    "severity": p.severity,
                    "current_solutions": p.current_solutions,
                    "why_insufficient": p.why_insufficient
                }
                for p in analyzer.get_top_n_pain_points(20)
            ]
            print(format_json_output(pain_points))
        else:
            list_pain_points()
    
    elif args.command == 'ideas':
        if args.json:
            generator = ProductIdeaGenerator()
            ideas = [
                {
                    "name": idea.name,
                    "description": idea.description,
                    "target_audience": idea.target_audience,
                    "monetization_model": idea.monetization_model.value,
                    "pricing_strategy": idea.pricing_strategy,
                    "key_features": idea.key_features,
                    "differentiation": idea.differentiation,
                    "estimated_mvp_months": idea.estimated_mvp_months,
                    "potential_score": generator.score_idea_potential(idea)
                }
                for idea in generator.generate_all_ideas()
            ]
            print(format_json_output(ideas))
        else:
            list_ideas()
    
    elif args.command == 'recommendations':
        if args.json:
            orchestrator = MarketIntelligenceOrchestrator()
            print(format_json_output({"recommendations": orchestrator.get_quick_recommendations(10)}))
        else:
            print_quick_recommendations()
    
    elif args.command == 'analyze':
        if not args.argument:
            print("Error: Please provide a trend name to analyze")
            parser.print_help()
            sys.exit(1)
        
        if args.json:
            orchestrator = MarketIntelligenceOrchestrator()
            print(format_json_output(orchestrator.generate_comprehensive_report(args.argument)))
        else:
            print_trend_report(args.argument)
    
    elif args.command == 'export':
        if not args.argument:
            print("Error: Please provide an output file path")
            parser.print_help()
            sys.exit(1)
        
        export_report(args.argument, args.format)


if __name__ == "__main__":
    main()
