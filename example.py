#!/usr/bin/env python3
"""
Example: Programmatic Usage of Solana Wallet Tracker
"""

from tracker import SolanaWalletTracker

def analyze_wallet_example():
    """
    Example of analyzing a wallet programmatically.
    """
    # Initialize the tracker
    tracker = SolanaWalletTracker()

    # Example wallet address (Jupiter Aggregator)
    wallet_address = "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"

    print(f"\n{'='*70}")
    print(f"EXAMPLE: Analyzing {wallet_address}")
    print(f"{'='*70}\n")

    # Perform analysis
    results = tracker.analyze_wallet(wallet_address, deep=False)

    # Access specific results
    if results:
        print("\n📊 EXTRACTED INSIGHTS:")

        # Balance
        balance = results.get('wallet_analysis', {}).get('balance', {})
        print(f"\n💰 Balance: {balance.get('formatted', 'N/A')}")

        # Transaction count
        total_txs = results.get('wallet_analysis', {}).get('total_transactions', 0)
        print(f"📝 Total Transactions: {total_txs:,}")

        # Performance score
        perf = results.get('performance_score', {})
        if perf:
            print(f"⭐ Performance Score: {perf.get('total_score', 0):.1f}/100 ({perf.get('tier', 'N/A')})")

        # Win rate
        pnl = results.get('pnl_data', {})
        if pnl:
            win_rate = pnl.get('win_rate', 0) * 100
            print(f"📈 Win Rate: {win_rate:.1f}%")

        # Risk score
        risk = results.get('wallet_risk', {})
        if risk:
            print(f"⚠️  Risk Score: {risk.get('risk_score', 0):.0f}/100 ({risk.get('risk_level', 'N/A')})")

        # Emerging tokens
        tokens = results.get('emerging_tokens', [])
        if tokens:
            print(f"\n🚀 Emerging Tokens Detected: {len(tokens)}")
            for i, token in enumerate(tokens[:3], 1):
                score = token['opportunity_score']['score']
                print(f"   {i}. Score: {score}/100 - {token['token_address'][:16]}...")

        # Display full results
        print(f"\n{'='*70}")
        print("FULL ANALYSIS REPORT:")
        print(f"{'='*70}")
        tracker.display_results(results)

    else:
        print("❌ Analysis failed - no results returned")

def batch_analysis_example():
    """
    Example of analyzing multiple wallets.
    """
    tracker = SolanaWalletTracker()

    wallets = [
        "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4",  # Jupiter
        # Add more wallet addresses here
    ]

    results_list = []

    for wallet in wallets:
        print(f"\n{'='*70}")
        print(f"Analyzing: {wallet}")
        print(f"{'='*70}")

        results = tracker.analyze_wallet(wallet, deep=False)
        results_list.append({
            'address': wallet,
            'results': results
        })

    # Compare results
    print(f"\n{'='*70}")
    print("COMPARISON SUMMARY")
    print(f"{'='*70}\n")

    for item in results_list:
        addr = item['address'][:16] + "..."
        results = item['results']

        perf_score = results.get('performance_score', {}).get('total_score', 0)
        risk_score = results.get('wallet_risk', {}).get('risk_score', 0)

        print(f"{addr}: Performance={perf_score:.0f} | Risk={risk_score:.0f}")

if __name__ == '__main__':
    print("\n" + "="*70)
    print("SOLANA WALLET TRACKER - PROGRAMMATIC EXAMPLE")
    print("="*70)

    # Choose example to run
    print("\n1. Single Wallet Analysis")
    print("2. Batch Analysis (Multiple Wallets)")

    choice = input("\nSelect example (1 or 2): ").strip()

    if choice == '1':
        analyze_wallet_example()
    elif choice == '2':
        batch_analysis_example()
    else:
        print("Invalid choice. Running single wallet example...")
        analyze_wallet_example()
