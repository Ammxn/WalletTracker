#!/usr/bin/env python3
"""
Solana Wallet Tracker - Web Interface (Streamlit)
Deploy to Streamlit Cloud, Railway, or Render in 1 minute!
"""

import streamlit as st
import sys
from io import StringIO
from tracker import SolanaWalletTracker
from utils import is_valid_solana_address
import config

# Page config
st.set_page_config(
    page_title="Solana Wallet Tracker",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .disclaimer {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-size: 1.2rem;
        padding: 0.75rem;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://cryptologos.cc/logos/solana-sol-logo.png", width=100)
    st.title("🚀 Solana Wallet Tracker")
    st.markdown("---")

    st.subheader("📋 Features")
    st.markdown("""
    - 🌊 **Flow Routing** - Multi-hop tracing
    - 📊 **Pattern Detection** - Clusters & heatmaps
    - 🚀 **Early Tokens** - Launch detection
    - ⚠️ **Risk Assessment** - Rug-pull indicators
    - 💰 **PnL Analysis** - Win rates & performance
    """)

    st.markdown("---")
    st.subheader("🎯 Quick Examples")
    example_wallets = {
        "Random Wallet 1": "HN7cABqLq46Es1jh92dQQisAq662SmxELLLsHHe4YWrH",
        "Random Wallet 2": "5Q544fKrFoe3tsEbD7S8EmxGTJYAKtddgY7qSqCCAT8f",
    }

    for name, addr in example_wallets.items():
        if st.button(name, key=f"ex_{addr}"):
            st.session_state.wallet_address = addr

    st.markdown("---")
    st.caption("⚠️ Educational tool only. Not financial advice.")

# Main content
st.markdown('<div class="main-header">🚀 Solana Wallet Tracker</div>', unsafe_allow_html=True)
st.markdown("### Analyze any Solana wallet with advanced on-chain intelligence")

# Disclaimer
with st.expander("⚠️ IMPORTANT DISCLAIMER - READ FIRST", expanded=False):
    st.markdown(config.DISCLAIMER)

# Input section
col1, col2 = st.columns([4, 1])

with col1:
    wallet_address = st.text_input(
        "Enter Solana Wallet Address:",
        value=st.session_state.get('wallet_address', ''),
        placeholder="e.g., 5Q544fKrFoe3tsEbD7S8EmxGTJYAKtddgY7qSqCCAT8f",
        help="Paste any Solana wallet address (Base58, 32-44 characters)"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    analyze_button = st.button("🔍 Analyze", type="primary", use_container_width=True)

# Analysis section
if analyze_button and wallet_address:
    if not is_valid_solana_address(wallet_address):
        st.error("❌ Invalid Solana address! Please check and try again.")
    else:
        # Create tabs for different sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview",
            "🌊 Flow Analysis",
            "📈 Patterns",
            "🚀 Early Tokens",
            "⚠️ Risk Assessment"
        ])

        # Progress
        with st.spinner("🔍 Analyzing wallet... This may take 30-60 seconds..."):
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Initialize tracker
            tracker = SolanaWalletTracker()

            # Capture output
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()

            try:
                # Run analysis with progress updates
                status_text.text("📡 Fetching wallet data...")
                progress_bar.progress(10)

                results = tracker.analyze_wallet(wallet_address, deep=False)

                progress_bar.progress(100)
                status_text.text("✅ Analysis complete!")

                # Restore stdout
                sys.stdout = old_stdout

                if not results:
                    st.error("❌ Failed to analyze wallet. Please try again.")
                else:
                    # Tab 1: Overview
                    with tab1:
                        st.subheader("📊 Wallet Overview")

                        # Key metrics
                        col1, col2, col3, col4 = st.columns(4)

                        wallet_data = results.get('wallet_analysis', {})
                        balance = wallet_data.get('balance', {})
                        perf_score = results.get('performance_score', {})
                        risk = results.get('wallet_risk', {})

                        with col1:
                            st.metric(
                                "💰 Balance",
                                balance.get('formatted', '0 SOL')
                            )

                        with col2:
                            st.metric(
                                "📝 Transactions",
                                f"{wallet_data.get('total_transactions', 0):,}"
                            )

                        with col3:
                            st.metric(
                                "⭐ Performance",
                                f"{perf_score.get('total_score', 0):.0f}/100",
                                perf_score.get('tier', 'N/A')
                            )

                        with col4:
                            risk_score = risk.get('risk_score', 0)
                            risk_level = risk.get('risk_level', 'UNKNOWN')
                            risk_color = "🟢" if risk_level == "LOW" else "🟡" if risk_level == "MEDIUM" else "🔴"
                            st.metric(
                                "⚠️ Risk",
                                f"{risk_color} {risk_level}",
                                f"{risk_score:.0f}/100"
                            )

                        st.markdown("---")

                        # Performance breakdown
                        st.subheader("📈 Performance Breakdown")
                        pnl_data = results.get('pnl_data', {})

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            win_rate = pnl_data.get('win_rate', 0) * 100
                            st.metric("Win Rate", f"{win_rate:.1f}%")

                        with col2:
                            st.metric("Total Trades", pnl_data.get('total_trades', 0))

                        with col3:
                            profit = pnl_data.get('total_profit_sol', 0)
                            st.metric("Total P&L", f"{profit:+.4f} SOL")

                        # Progress bar for win rate
                        st.progress(win_rate / 100)
                        st.caption(f"✅ Wins: {pnl_data.get('wins', 0)} | ❌ Losses: {pnl_data.get('losses', 0)}")

                    # Tab 2: Flow Analysis
                    with tab2:
                        st.subheader("🌊 Transaction Flow Analysis")

                        flow_data = results.get('flow_data', {})
                        account_flows = flow_data.get('account_flows', {})

                        if account_flows:
                            # Top inflows
                            st.markdown("#### 🔽 Top Inflows")
                            top_inflows = sorted(
                                account_flows.items(),
                                key=lambda x: x[1]['inflows'],
                                reverse=True
                            )[:5]

                            for addr, flows in top_inflows:
                                col1, col2, col3 = st.columns([3, 1, 1])
                                with col1:
                                    st.code(addr[:16] + "...")
                                with col2:
                                    st.success(f"+{flows['inflows']:.4f} SOL")
                                with col3:
                                    net = flows['net']
                                    st.metric("Net", f"{net:+.4f}")

                            st.markdown("---")

                            # Top outflows
                            st.markdown("#### 🔼 Top Outflows")
                            top_outflows = sorted(
                                account_flows.items(),
                                key=lambda x: x[1]['outflows'],
                                reverse=True
                            )[:5]

                            for addr, flows in top_outflows:
                                col1, col2, col3 = st.columns([3, 1, 1])
                                with col1:
                                    st.code(addr[:16] + "...")
                                with col2:
                                    st.error(f"-{flows['outflows']:.4f} SOL")
                                with col3:
                                    net = flows['net']
                                    st.metric("Net", f"{net:+.4f}")
                        else:
                            st.info("No significant flow data available for this wallet.")

                    # Tab 3: Patterns
                    with tab3:
                        st.subheader("📈 Pattern Analysis")

                        # Clustering
                        cluster_data = results.get('cluster_data', {})
                        st.markdown("#### 🔗 Wallet Clustering")

                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric(
                                "Clustered Wallets",
                                cluster_data.get('total_clusters', 0)
                            )
                        with col2:
                            interconnect = cluster_data.get('interconnectedness_pct', 0)
                            st.metric(
                                "Interconnectedness",
                                f"{interconnect:.1f}%"
                            )

                        st.caption(cluster_data.get('assessment', 'N/A'))

                        st.markdown("---")

                        # Temporal patterns
                        temporal_data = results.get('temporal_data', {})
                        st.markdown("#### 🕐 Activity Patterns")

                        if temporal_data:
                            peak_hour = temporal_data.get('peak_hour', 0)
                            peak_count = temporal_data.get('peak_count', 0)

                            st.info(f"📍 Peak Activity: {peak_hour:02d}:00 UTC ({peak_count} transactions)")

                            bursts = temporal_data.get('bursts', [])
                            if bursts:
                                st.warning(f"⚡ Detected {len(bursts)} burst periods")

                    # Tab 4: Early Tokens
                    with tab4:
                        st.subheader("🚀 Early Token Opportunities")

                        emerging_tokens = results.get('emerging_tokens', [])

                        if emerging_tokens:
                            for i, token in enumerate(emerging_tokens[:5], 1):
                                with st.expander(f"Token #{i} - Score: {token['opportunity_score']['score']}/100"):
                                    st.code(f"Address: {token['token_address']}")

                                    score = token['opportunity_score']

                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.metric("Opportunity Level", score['opportunity_level'])
                                    with col2:
                                        st.metric("Score", f"{score['score']}/100")

                                    st.info(score['recommendation'])

                                    st.markdown("**Factors:**")
                                    for factor in score.get('factors', []):
                                        st.caption(f"• {factor}")
                        else:
                            st.info("ℹ️ No early token entries detected in recent activity.")

                    # Tab 5: Risk Assessment
                    with tab5:
                        st.subheader("⚠️ Risk Assessment")

                        risk = results.get('wallet_risk', {})

                        # Risk gauge
                        risk_score = risk.get('risk_score', 0)
                        risk_level = risk.get('risk_level', 'UNKNOWN')

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Risk Score", f"{risk_score:.0f}/100")
                        with col2:
                            risk_color = "🟢" if risk_level == "LOW" else "🟡" if risk_level == "MEDIUM" else "🔴"
                            st.metric("Risk Level", f"{risk_color} {risk_level}")
                        with col3:
                            anomaly_count = risk.get('anomaly_count', 0)
                            st.metric("Anomalies", anomaly_count)

                        st.progress(risk_score / 100)

                        st.markdown("---")

                        st.markdown("#### 🚨 Risk Factors")
                        factors = risk.get('factors', [])
                        if factors:
                            for factor in factors:
                                st.warning(f"• {factor}")
                        else:
                            st.success("✅ No significant risk factors detected")

                        st.markdown("---")

                        st.markdown("#### 📋 Risk Management Recommendations")
                        st.markdown("""
                        - Always DYOR (Do Your Own Research)
                        - Never invest more than you can afford to lose
                        - Use stop-losses: -10-20% for high-risk plays
                        - Diversify: Limit single position to 1-5% of portfolio
                        - Verify token contracts independently
                        """)

            except Exception as e:
                sys.stdout = old_stdout
                st.error(f"❌ Error during analysis: {str(e)}")
                st.exception(e)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🔗 [GitHub](https://github.com)")
with col2:
    st.caption("📚 [Documentation](README.md)")
with col3:
    st.caption("⚠️ Educational purposes only")

# Initialize session state
if 'wallet_address' not in st.session_state:
    st.session_state.wallet_address = ""
