"""
Pattern Recognition System
Clustering, heatmaps, PnL scoring, and behavioral analysis
"""

from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter
from datetime import datetime, timezone
import pandas as pd
import numpy as np
import config
from utils import aggregate_pnl, calculate_pnl, format_timestamp

class PatternDetector:
    """
    Advanced pattern recognition for wallet behavior analysis.
    Detects clusters, temporal patterns, PnL performance, and anomalies.
    """

    def __init__(self):
        self.patterns = {}
        self.clusters = {}
        self.performance_scores = {}

    def detect_wallet_clusters(
        self,
        transactions: List[Dict],
        counterparties: Dict[str, int],
        min_shared_txs: int = None
    ) -> Dict[str, Any]:
        """
        Detect wallet clusters based on shared transaction patterns.

        Args:
            transactions: List of parsed transactions
            counterparties: Dict of counterparty addresses and interaction counts
            min_shared_txs: Minimum shared transactions to form cluster

        Returns:
            Dict with cluster information
        """
        if min_shared_txs is None:
            min_shared_txs = config.ANALYSIS_CONFIG['cluster_min_shared_txs']

        print(f"\n🔗 Detecting wallet clusters (min {min_shared_txs} shared txs)...")

        # Filter high-frequency counterparties
        clustered_wallets = {
            addr: count for addr, count in counterparties.items()
            if count >= min_shared_txs
        }

        # Calculate cluster strength score
        cluster_data = []
        for addr, count in clustered_wallets.items():
            strength = min(count / 50.0, 1.0)  # Normalize to 0-1
            cluster_data.append({
                'address': addr,
                'shared_transactions': count,
                'strength_score': strength,
                'link_type': self._classify_link_type(count)
            })

        # Sort by strength
        cluster_data = sorted(
            cluster_data,
            key=lambda x: x['shared_transactions'],
            reverse=True
        )

        # Calculate interconnectedness
        total_counterparties = len(counterparties)
        highly_connected = len(clustered_wallets)
        interconnectedness_pct = (
            highly_connected / total_counterparties * 100
            if total_counterparties > 0 else 0
        )

        print(f"✅ Found {len(cluster_data)} clustered wallets")
        print(f"   Interconnectedness: {interconnectedness_pct:.1f}%")

        return {
            'clustered_wallets': cluster_data,
            'total_clusters': len(cluster_data),
            'interconnectedness_pct': interconnectedness_pct,
            'assessment': self._assess_clustering(interconnectedness_pct)
        }

    def _classify_link_type(self, count: int) -> str:
        """Classify connection strength."""
        if count >= 20:
            return "STRONG"
        elif count >= 10:
            return "MODERATE"
        elif count >= 5:
            return "WEAK"
        else:
            return "MINIMAL"

    def _assess_clustering(self, interconnectedness_pct: float) -> str:
        """Assess overall clustering significance."""
        if interconnectedness_pct >= 15:
            return "High network coordination detected"
        elif interconnectedness_pct >= 8:
            return "Moderate group activity patterns"
        elif interconnectedness_pct >= 3:
            return "Some coordinated behavior"
        else:
            return "Mostly independent activity"

    def generate_temporal_heatmap(
        self,
        transactions: List[Dict]
    ) -> Dict[str, Any]:
        """
        Generate temporal activity heatmap.
        Analyzes transaction timing patterns by hour and day.

        Returns:
            Dict with hourly/daily activity patterns and burst detection
        """
        print(f"\n🕐 Generating temporal heatmap...")

        if not transactions:
            return {}

        # Convert timestamps to datetime
        tx_times = []
        for tx in transactions:
            if 'timestamp' in tx and tx['timestamp']:
                dt = datetime.fromtimestamp(tx['timestamp'], tz=timezone.utc)
                tx_times.append({
                    'datetime': dt,
                    'hour': dt.hour,
                    'day': dt.weekday(),
                    'timestamp': tx['timestamp']
                })

        if not tx_times:
            return {}

        # Create DataFrame for analysis
        df = pd.DataFrame(tx_times)

        # Hourly distribution
        hourly_counts = df['hour'].value_counts().sort_index()
        hourly_data = {hour: hourly_counts.get(hour, 0) for hour in range(24)}

        # Daily distribution (0=Monday, 6=Sunday)
        daily_counts = df['day'].value_counts().sort_index()
        daily_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        daily_data = {
            daily_names[day]: daily_counts.get(day, 0)
            for day in range(7)
        }

        # Detect bursts (periods with high activity)
        burst_threshold = config.ANALYSIS_CONFIG['pattern_burst_threshold']
        bursts = []

        for hour, count in hourly_data.items():
            if count >= burst_threshold:
                bursts.append({
                    'hour': hour,
                    'count': count,
                    'intensity': 'HIGH' if count >= burst_threshold * 2 else 'MODERATE'
                })

        # Peak activity hour
        peak_hour = max(hourly_data.items(), key=lambda x: x[1])

        print(f"✅ Peak activity: {peak_hour[1]} txs at {peak_hour[0]:02d}:00 UTC")
        if bursts:
            print(f"   Detected {len(bursts)} burst periods")

        return {
            'hourly_distribution': hourly_data,
            'daily_distribution': daily_data,
            'bursts': bursts,
            'peak_hour': peak_hour[0],
            'peak_count': peak_hour[1],
            'total_analyzed': len(tx_times),
            'pattern_type': self._classify_temporal_pattern(hourly_data, bursts)
        }

    def _classify_temporal_pattern(
        self,
        hourly_data: Dict[int, int],
        bursts: List[Dict]
    ) -> str:
        """Classify temporal activity pattern."""
        if len(bursts) >= 3:
            return "BURST_ACTIVITY - Potential coordinated timing"
        elif max(hourly_data.values()) > sum(hourly_data.values()) * 0.3:
            return "CONCENTRATED - Activity focused in specific hours"
        else:
            return "DISTRIBUTED - Activity spread throughout day"

    def calculate_wallet_pnl(
        self,
        transactions: List[Dict],
        price_data: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Calculate approximate PnL from transaction history.
        Estimates profit/loss based on balance changes.

        Args:
            transactions: List of parsed transactions
            price_data: Optional dict of token prices for valuation

        Returns:
            Dict with PnL metrics and win rate
        """
        print(f"\n💰 Calculating wallet PnL...")

        trades = []
        total_profit_sol = 0

        for tx in transactions:
            if not tx.get('success', False):
                continue

            pre_balances = tx.get('pre_balances', [])
            post_balances = tx.get('post_balances', [])

            # Calculate net balance change (excluding fees)
            if pre_balances and post_balances:
                # Primary account (index 0) balance change
                if len(pre_balances) > 0 and len(post_balances) > 0:
                    pre = pre_balances[0] / 1e9
                    post = post_balances[0] / 1e9
                    delta = post - pre
                    fee = tx.get('fee', 0) / 1e9

                    # Positive delta = profit, negative = loss
                    if abs(delta) > fee:  # Ignore fee-only transactions
                        net_profit = delta + fee  # Add fee back since it's a cost

                        trades.append({
                            'signature': tx.get('signature', 'Unknown'),
                            'timestamp': tx.get('timestamp', 0),
                            'profit': net_profit,
                            'roi_pct': 0,  # Would need entry price for accurate ROI
                            'win': net_profit > 0
                        })

                        total_profit_sol += net_profit

        # Aggregate statistics
        pnl_stats = aggregate_pnl(trades)
        pnl_stats['total_profit_sol'] = total_profit_sol

        # Performance classification
        win_rate = pnl_stats.get('win_rate', 0)
        pnl_stats['performance_tier'] = self._classify_performance(win_rate)

        print(f"✅ Analyzed {len(trades)} trades")
        print(f"   Win Rate: {win_rate*100:.1f}%")
        print(f"   Total P&L: {total_profit_sol:+.4f} SOL")

        return pnl_stats

    def _classify_performance(self, win_rate: float) -> str:
        """Classify wallet performance tier."""
        threshold = config.ANALYSIS_CONFIG['pnl_win_threshold']

        if win_rate >= threshold:
            return "HIGH_PERFORMER"
        elif win_rate >= 0.6:
            return "ABOVE_AVERAGE"
        elif win_rate >= 0.45:
            return "AVERAGE"
        else:
            return "BELOW_AVERAGE"

    def detect_anomalies(self, transactions: List[Dict]) -> List[Dict]:
        """
        Detect anomalous transaction patterns.
        Flags unusual behavior like wash trading, suspicious timing, etc.

        Returns:
            List of detected anomalies
        """
        print(f"\n🚨 Detecting anomalies...")

        anomalies = []

        if not transactions:
            return anomalies

        # Check for rapid back-and-forth transactions (potential wash trading)
        account_interactions = defaultdict(list)

        for tx in transactions:
            accounts = tx.get('accounts', [])
            timestamp = tx.get('timestamp', 0)

            for account in accounts:
                account_interactions[account].append(timestamp)

        # Detect rapid repeated interactions
        for account, timestamps in account_interactions.items():
            if len(timestamps) >= 5:
                sorted_times = sorted(timestamps)
                # Check for 5+ interactions within 60 seconds
                for i in range(len(sorted_times) - 4):
                    time_window = sorted_times[i+4] - sorted_times[i]
                    if time_window <= 60:
                        anomalies.append({
                            'type': 'RAPID_INTERACTIONS',
                            'account': account,
                            'count': 5,
                            'time_window': time_window,
                            'severity': 'MEDIUM',
                            'description': f'5 interactions within {time_window}s - possible wash trading'
                        })
                        break

        # Detect identical transaction patterns
        tx_patterns = []
        for tx in transactions:
            pattern = f"{len(tx.get('accounts', []))}_{len(tx.get('programs', []))}"
            tx_patterns.append(pattern)

        pattern_counts = Counter(tx_patterns)
        for pattern, count in pattern_counts.items():
            if count >= 10:
                anomalies.append({
                    'type': 'REPETITIVE_PATTERN',
                    'pattern': pattern,
                    'count': count,
                    'severity': 'LOW',
                    'description': f'Identical transaction structure repeated {count} times'
                })

        if anomalies:
            print(f"⚠️  Found {len(anomalies)} anomalies")
        else:
            print(f"✅ No significant anomalies detected")

        return anomalies

    def score_wallet_performance(
        self,
        pnl_data: Dict,
        cluster_data: Dict,
        temporal_data: Dict
    ) -> Dict[str, Any]:
        """
        Generate comprehensive performance score for wallet.
        Combines PnL, clustering, and temporal patterns.

        Returns:
            Dict with overall score and breakdown
        """
        print(f"\n⭐ Calculating performance score...")

        scores = {}

        # PnL score (0-40 points)
        win_rate = pnl_data.get('win_rate', 0)
        pnl_score = min(win_rate * 40, 40)
        scores['pnl'] = pnl_score

        # Cluster score (0-30 points) - higher interconnectedness = higher score
        interconnect_pct = cluster_data.get('interconnectedness_pct', 0)
        cluster_score = min(interconnect_pct * 2, 30)
        scores['cluster'] = cluster_score

        # Activity score (0-30 points) - consistent activity = higher score
        bursts = temporal_data.get('bursts', [])
        burst_score = min(len(bursts) * 3, 15)
        total_txs = temporal_data.get('total_analyzed', 0)
        activity_score = min(total_txs / 10, 15)
        scores['temporal'] = burst_score + activity_score

        # Total score
        total_score = sum(scores.values())

        # Classification
        if total_score >= 75:
            tier = "ELITE"
            assessment = "Notable high-performance wallet"
        elif total_score >= 60:
            tier = "ADVANCED"
            assessment = "Above-average performance metrics"
        elif total_score >= 40:
            tier = "INTERMEDIATE"
            assessment = "Moderate activity and performance"
        else:
            tier = "BASIC"
            assessment = "Standard wallet activity"

        print(f"✅ Overall Score: {total_score:.1f}/100 ({tier})")

        return {
            'total_score': total_score,
            'tier': tier,
            'assessment': assessment,
            'breakdown': scores,
            'metrics': {
                'win_rate': win_rate,
                'interconnectedness': interconnect_pct,
                'burst_count': len(bursts),
                'total_transactions': total_txs
            }
        }

    def generate_pattern_summary(
        self,
        cluster_data: Dict,
        temporal_data: Dict,
        pnl_data: Dict,
        anomalies: List[Dict]
    ) -> str:
        """
        Generate comprehensive pattern analysis summary.

        Returns:
            Formatted text summary
        """
        lines = []
        lines.append(f"\n{'='*70}")
        lines.append(f"📈 PATTERN ANALYSIS SUMMARY")
        lines.append(f"{'='*70}")

        # Clustering
        lines.append(f"\n🔗 WALLET CLUSTERING:")
        cluster_count = cluster_data.get('total_clusters', 0)
        interconnect = cluster_data.get('interconnectedness_pct', 0)
        lines.append(f"   Clustered Wallets: {cluster_count}")
        lines.append(f"   Interconnectedness: {interconnect:.1f}%")
        lines.append(f"   Assessment: {cluster_data.get('assessment', 'N/A')}")

        # Temporal patterns
        lines.append(f"\n🕐 TEMPORAL PATTERNS:")
        peak_hour = temporal_data.get('peak_hour', 0)
        peak_count = temporal_data.get('peak_count', 0)
        bursts = temporal_data.get('bursts', [])
        lines.append(f"   Peak Activity: {peak_hour:02d}:00 UTC ({peak_count} txs)")
        lines.append(f"   Burst Periods: {len(bursts)}")
        lines.append(f"   Pattern: {temporal_data.get('pattern_type', 'N/A')}")

        # PnL Performance
        lines.append(f"\n💰 PERFORMANCE METRICS:")
        win_rate = pnl_data.get('win_rate', 0)
        total_trades = pnl_data.get('total_trades', 0)
        lines.append(f"   Win Rate: {win_rate*100:.1f}% ({pnl_data.get('wins', 0)}/{total_trades})")
        lines.append(f"   Performance Tier: {pnl_data.get('performance_tier', 'N/A')}")

        # Anomalies
        if anomalies:
            lines.append(f"\n🚨 ANOMALIES DETECTED:")
            for anomaly in anomalies[:3]:
                lines.append(f"   • {anomaly['type']}: {anomaly['description']}")

        return '\n'.join(lines)
