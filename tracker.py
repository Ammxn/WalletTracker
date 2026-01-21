#!/usr/bin/env python3
"""
Solana Wallet Tracker - Main CLI Interface
Ultimate 2026 Edition with Advanced Flow Routing and AI-Powered Analysis
"""

import sys
import argparse
from typing import Optional, List
import config
from utils import is_valid_solana_address, extract_addresses, format_table_data
from wallet_analyzer import WalletAnalyzer
from flow_router import FlowRouter
from pattern_detector import PatternDetector
from early_detector import EarlyTokenDetector
from risk_assessor import RiskAssessor
from visualizer import Visualizer

class SolanaWalletTracker:
    """
    Main tracker class - orchestrates all analysis modules.
    """

    def __init__(self):
        print(config.DISCLAIMER)
        print("\n🚀 Initializing Solana Elite Analyzer...")

        self.wallet_analyzer = WalletAnalyzer()
        self.flow_router = FlowRouter()
        self.pattern_detector = PatternDetector()
        self.early_detector = EarlyTokenDetector()
        self.risk_assessor = RiskAssessor()
        self.visualizer = Visualizer()

        print("✅ All modules loaded successfully\n")

    def analyze_wallet(self, address: str, deep: bool = False) -> dict:
        """
        Comprehensive wallet analysis.

        Args:
            address: Solana wallet address
            deep: If True, perform deeper analysis (more API calls, longer processing)

        Returns:
            Dict with complete analysis results
        """
        if not is_valid_solana_address(address):
            print(f"❌ Invalid Solana address: {address}")
            return {}

        print(f"\n🎯 Starting comprehensive analysis of wallet: {address}")
        print(f"{'='*70}\n")

        results = {}

        # Step 1: Basic wallet analysis
        print("📍 Step 1/7: Fetching wallet data...")
        wallet_data = self.wallet_analyzer.analyze_wallet(address)
        results['wallet_analysis'] = wallet_data

        if not wallet_data:
            print("❌ Failed to retrieve wallet data")
            return results

        # Step 2: Flow routing analysis
        print("\n📍 Step 2/7: Analyzing transaction flows...")
        transactions = wallet_data.get('parsed_transactions', [])
        flow_data = self.flow_router.trace_flows(transactions)
        results['flow_data'] = flow_data

        # Find counterparties for clustering
        counterparties = self.flow_router.find_counterparties(transactions, address)
        results['counterparties'] = counterparties

        # Multi-hop chains
        multi_hop = self.flow_router.identify_multi_hop_chains(transactions, min_hops=2)
        results['multi_hop_chains'] = multi_hop

        # Step 3: Pattern detection
        print("\n📍 Step 3/7: Detecting patterns...")

        # Clustering
        cluster_data = self.pattern_detector.detect_wallet_clusters(
            transactions, counterparties
        )
        results['cluster_data'] = cluster_data

        # Temporal heatmap
        temporal_data = self.pattern_detector.generate_temporal_heatmap(transactions)
        results['temporal_data'] = temporal_data

        # PnL calculation
        pnl_data = self.pattern_detector.calculate_wallet_pnl(transactions)
        results['pnl_data'] = pnl_data

        # Anomaly detection
        anomalies = self.pattern_detector.detect_anomalies(transactions)
        results['anomalies'] = anomalies

        # Step 4: Performance scoring
        print("\n📍 Step 4/7: Calculating performance score...")
        performance_score = self.pattern_detector.score_wallet_performance(
            pnl_data, cluster_data, temporal_data
        )
        results['performance_score'] = performance_score

        # Step 5: Early token detection
        print("\n📍 Step 5/7: Searching for early token opportunities...")
        emerging_tokens = self.early_detector.find_emerging_tokens(transactions)
        results['emerging_tokens'] = emerging_tokens

        # Step 6: Risk assessment
        print("\n📍 Step 6/7: Assessing risks...")
        wallet_risk = self.risk_assessor.assess_wallet_risk(wallet_data, anomalies)
        results['wallet_risk'] = wallet_risk

        # Token risks (for emerging tokens)
        token_risks = []
        for token in emerging_tokens[:3]:  # Limit to avoid excessive API calls
            token_info = token.get('token_info')
            if token_info:
                risk = self.risk_assessor.assess_token_risk(token_info)
                token_risks.append(risk)
        results['token_risks'] = token_risks

        # Rug-pull indicators
        rug_indicators = []
        for token in emerging_tokens[:3]:
            indicators = self.risk_assessor.detect_rug_pull_indicators(
                token.get('token_info'),
                transactions
            )
            rug_indicators.extend(indicators)
        results['rug_indicators'] = rug_indicators

        # Step 7: Generate reports
        print("\n📍 Step 7/7: Generating comprehensive report...")

        print("\n" + "="*70)
        print("✅ ANALYSIS COMPLETE")
        print("="*70)

        return results

    def display_results(self, results: dict):
        """
        Display formatted analysis results.

        Args:
            results: Analysis results dictionary
        """
        if not results:
            return

        # Summary dashboard
        dashboard = self.visualizer.create_summary_dashboard(results)
        print(dashboard)

        # Flow summary
        if 'flow_data' in results:
            flow_summary = self.flow_router.generate_flow_summary(results['flow_data'])
            print(flow_summary)

            # Flow diagram
            routes = results['flow_data'].get('routes', [])
            if routes:
                flow_diagram = self.visualizer.create_flow_diagram(routes, limit=10)
                print(flow_diagram)

        # Multi-hop chains
        if results.get('multi_hop_chains'):
            print(f"\n{'='*70}")
            print(f"🔗 MULTI-HOP TRANSACTION CHAINS")
            print(f"{'='*70}")
            for i, chain in enumerate(results['multi_hop_chains'][:5], 1):
                print(f"\n{i}. {chain['hop_count']} hops:")
                print(f"   {chain['chain']}")
                print(f"   Tx: {chain['signature'][:16]}...")

        # Pattern analysis summary
        if all(k in results for k in ['cluster_data', 'temporal_data', 'pnl_data']):
            pattern_summary = self.pattern_detector.generate_pattern_summary(
                results['cluster_data'],
                results['temporal_data'],
                results['pnl_data'],
                results.get('anomalies', [])
            )
            print(pattern_summary)

        # Temporal heatmap
        if 'temporal_data' in results:
            hourly_data = results['temporal_data'].get('hourly_distribution', {})
            if hourly_data:
                heatmap = self.visualizer.create_heatmap(hourly_data)
                print(heatmap)

        # Cluster visualization
        if 'cluster_data' in results:
            cluster_viz = self.visualizer.create_cluster_visualization(results['cluster_data'])
            print(cluster_viz)

        # Performance chart
        if 'pnl_data' in results:
            perf_chart = self.visualizer.create_performance_chart(results['pnl_data'])
            print(perf_chart)

        # Early token report
        if 'emerging_tokens' in results:
            early_report = self.early_detector.generate_early_detection_report(
                results['emerging_tokens']
            )
            print(early_report)

        # Risk report
        if 'wallet_risk' in results:
            risk_report = self.risk_assessor.generate_risk_report(
                results['wallet_risk'],
                results.get('token_risks', []),
                results.get('rug_indicators', [])
            )
            print(risk_report)

        # Strategic observations
        self._display_strategic_observations(results)

    def _display_strategic_observations(self, results: dict):
        """
        Display educational strategic observations and insights.

        Args:
            results: Analysis results
        """
        print(f"\n{'='*70}")
        print(f"🎓 STRATEGIC OBSERVATIONS (Educational)")
        print(f"{'='*70}")

        performance_score = results.get('performance_score', {})
        pnl_data = results.get('pnl_data', {})
        cluster_data = results.get('cluster_data', {})

        # Performance-based insights
        tier = performance_score.get('tier', 'BASIC')
        win_rate = pnl_data.get('win_rate', 0)

        print(f"\n📊 PERFORMANCE PROFILE:")
        print(f"   This wallet exhibits {tier} performance characteristics.")

        if win_rate >= 0.75:
            print(f"\n   🌟 High Win Rate Detected ({win_rate*100:.1f}%):")
            print(f"      → Research Strategy: Analyze this wallet's entry/exit patterns")
            print(f"      → Consider similar tokens with small test positions (1-2%)")
            print(f"      → Set stop-losses at -10-20% to manage risk")
            print(f"      → Track for consistent patterns over multiple trades")

        # Clustering insights
        interconnect = cluster_data.get('interconnectedness_pct', 0)
        if interconnect >= 10:
            print(f"\n   🔗 Network Activity Detected ({interconnect:.1f}% interconnectedness):")
            print(f"      → Map the wallet cluster using tools like BubbleMaps")
            print(f"      → High coordination may indicate group accumulation")
            print(f"      → Cross-reference with on-chain volume for validation")
            print(f"      → View as 'strong network signal' for further research")

        # Early entry insights
        emerging_tokens = results.get('emerging_tokens', [])
        if emerging_tokens:
            high_opportunity = [t for t in emerging_tokens if t['opportunity_score']['score'] >= 60]
            if high_opportunity:
                print(f"\n   🚀 Early Entry Opportunities ({len(high_opportunity)} detected):")
                print(f"      → Framework: Enter post-liquidity add with balanced holders")
                print(f"      → Risk Management: Trail stops at +50% gains")
                print(f"      → Position Size: Limit to 1-3% of portfolio per token")
                print(f"      → Diversify across 3-5 signals to reduce single-token risk")

        # General wealth-building framework
        print(f"\n💎 WEALTH-BUILDING FRAMEWORK (Process-Oriented):")
        print(f"   1. Pattern Recognition:")
        print(f"      • Identify top wallets with >75% win rate (like this analysis)")
        print(f"      • Study their entry timing, position sizing, exit strategies")
        print(f"   2. Risk Management:")
        print(f"      • Diversify across 8-12 data-flagged opportunities")
        print(f"      • Never exceed 1-5% portfolio allocation per position")
        print(f"      • Use stop-losses religiously (-10-20%)")
        print(f"   3. Systematic Approach:")
        print(f"      • Reinvest 30% of gains, secure 70%")
        print(f"      • Build dashboard to track multiple high-performing wallets")
        print(f"      • Backtest strategies using historical Dune.com data")
        print(f"   4. Continuous Learning:")
        print(f"      • Review wins AND losses to refine criteria")
        print(f"      • Adjust strategy based on market conditions")
        print(f"      • Focus on consistent, low-risk wins vs. home runs")

        print(f"\n{'='*70}")
        print(f"⚠️  CRITICAL REMINDER:")
        print(f"These are EDUCATIONAL observations for building analytical skills.")
        print(f"All crypto investments carry significant risk. Past performance does")
        print(f"NOT guarantee future results. Always DYOR, diversify, and only risk")
        print(f"capital you can afford to lose completely.")
        print(f"{'='*70}\n")

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Solana Wallet Tracker - Ultimate 2026 Edition',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a specific wallet
  python tracker.py 5Q544fKrFoezxcGXoJwCAVQgTKi4DUgHV31QBBz7uRGj

  # Deep analysis (more thorough, slower)
  python tracker.py --deep <wallet_address>

  # Analyze multiple wallets
  python tracker.py <wallet1> <wallet2> <wallet3>

For more information, see README.md
        """
    )

    parser.add_argument(
        'addresses',
        nargs='+',
        help='One or more Solana wallet addresses to analyze'
    )

    parser.add_argument(
        '--deep',
        action='store_true',
        help='Perform deep analysis (more API calls, longer processing)'
    )

    parser.add_argument(
        '--no-display',
        action='store_true',
        help='Skip displaying results (useful for programmatic use)'
    )

    args = parser.parse_args()

    # Extract and validate addresses
    all_addresses = []
    for addr_input in args.addresses:
        addrs = extract_addresses(addr_input)
        all_addresses.extend(addrs)

    if not all_addresses:
        print("❌ No valid Solana addresses found in input")
        sys.exit(1)

    # Limit to 5 wallets to avoid excessive processing
    if len(all_addresses) > 5:
        print(f"⚠️  Limiting analysis to first 5 wallets (provided {len(all_addresses)})")
        all_addresses = all_addresses[:5]

    # Initialize tracker
    tracker = SolanaWalletTracker()

    # Analyze each wallet
    for address in all_addresses:
        try:
            results = tracker.analyze_wallet(address, deep=args.deep)

            if not args.no_display:
                tracker.display_results(results)

            print(f"\n{'='*70}")
            print(f"✅ Analysis complete for {address}")
            print(f"{'='*70}\n")

        except KeyboardInterrupt:
            print("\n\n⚠️  Analysis interrupted by user")
            sys.exit(0)

        except Exception as e:
            print(f"\n❌ Error analyzing {address}: {str(e)}")
            import traceback
            traceback.print_exc()
            continue

    print("\n🎉 All analyses complete!")
    print(config.DISCLAIMER)

if __name__ == '__main__':
    main()
