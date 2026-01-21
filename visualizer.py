"""
Visualization Module
Creates visual representations of flows, heatmaps, and patterns
"""

from typing import Dict, List, Any
import config
from utils import truncate_address

class Visualizer:
    """
    Create ASCII-based visualizations for terminal display.
    Includes flow graphs, heatmaps, and pattern charts.
    """

    def __init__(self):
        self.colors = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
            'reset': '\033[0m'
        }

    def colorize(self, text: str, color: str) -> str:
        """Add color to text for terminal display."""
        if color in self.colors:
            return f"{self.colors[color]}{text}{self.colors['reset']}"
        return text

    def create_heatmap(self, hourly_data: Dict[int, int]) -> str:
        """
        Create ASCII heatmap of hourly activity.

        Args:
            hourly_data: Dict mapping hour (0-23) to transaction count

        Returns:
            Formatted ASCII heatmap
        """
        if not hourly_data:
            return "No data for heatmap"

        max_count = max(hourly_data.values()) if hourly_data else 1
        bar_width = 40

        lines = []
        lines.append(f"\n{'='*70}")
        lines.append(f"📊 HOURLY ACTIVITY HEATMAP")
        lines.append(f"{'='*70}")

        for hour in range(24):
            count = hourly_data.get(hour, 0)
            bar_length = int((count / max_count) * bar_width) if max_count > 0 else 0
            bar = '█' * bar_length

            # Color based on intensity
            if count >= max_count * 0.7:
                bar = self.colorize(bar, 'red')
            elif count >= max_count * 0.4:
                bar = self.colorize(bar, 'yellow')
            else:
                bar = self.colorize(bar, 'green')

            lines.append(f"{hour:02d}:00 | {bar} {count}")

        lines.append(f"{'='*70}")

        return '\n'.join(lines)

    def create_flow_diagram(
        self,
        routes: List[Dict],
        limit: int = 10
    ) -> str:
        """
        Create ASCII flow diagram showing transaction routes.

        Args:
            routes: List of route dictionaries
            limit: Maximum routes to display

        Returns:
            Formatted ASCII flow diagram
        """
        if not routes:
            return "No flow data available"

        lines = []
        lines.append(f"\n{'='*70}")
        lines.append(f"🌊 TRANSACTION FLOW DIAGRAM")
        lines.append(f"{'='*70}")

        for i, route in enumerate(routes[:limit], 1):
            account = truncate_address(route['account'])
            amount = route['amount_sol']
            direction = route['direction']
            programs = route['programs']

            # Direction arrow and color
            if direction == 'INFLOW':
                arrow = '→'
                amount_str = self.colorize(f"+{amount:.4f} SOL", 'green')
            else:
                arrow = '←'
                amount_str = self.colorize(f"-{amount:.4f} SOL", 'red')

            lines.append(f"\n{i}. {account}")
            lines.append(f"   {arrow} {amount_str}")
            lines.append(f"   Via: {programs}")

        lines.append(f"\n{'='*70}")

        return '\n'.join(lines)

    def create_cluster_visualization(
        self,
        cluster_data: Dict
    ) -> str:
        """
        Create visualization of wallet clusters.

        Args:
            cluster_data: Cluster analysis data

        Returns:
            Formatted ASCII cluster diagram
        """
        clustered_wallets = cluster_data.get('clustered_wallets', [])

        if not clustered_wallets:
            return "\nNo significant clusters detected"

        lines = []
        lines.append(f"\n{'='*70}")
        lines.append(f"🔗 WALLET CLUSTER NETWORK")
        lines.append(f"{'='*70}")
        lines.append(f"Interconnectedness: {cluster_data.get('interconnectedness_pct', 0):.1f}%")

        for i, wallet in enumerate(clustered_wallets[:10], 1):
            addr = truncate_address(wallet['address'])
            count = wallet['shared_transactions']
            link_type = wallet['link_type']
            strength = wallet['strength_score']

            # Visual strength indicator
            strength_bar = '●' * int(strength * 10)

            # Color by link type
            if link_type == 'STRONG':
                strength_bar = self.colorize(strength_bar, 'red')
                link_color = 'red'
            elif link_type == 'MODERATE':
                strength_bar = self.colorize(strength_bar, 'yellow')
                link_color = 'yellow'
            else:
                strength_bar = self.colorize(strength_bar, 'green')
                link_color = 'green'

            link_text = self.colorize(link_type, link_color)

            lines.append(f"\n{i}. {addr}")
            lines.append(f"   Shared Txs: {count} | Strength: {strength_bar} ({link_text})")

        lines.append(f"\n{'='*70}")

        return '\n'.join(lines)

    def create_performance_chart(
        self,
        pnl_data: Dict
    ) -> str:
        """
        Create performance metrics visualization.

        Args:
            pnl_data: PnL analysis data

        Returns:
            Formatted ASCII performance chart
        """
        lines = []
        lines.append(f"\n{'='*70}")
        lines.append(f"📈 PERFORMANCE METRICS")
        lines.append(f"{'='*70}")

        win_rate = pnl_data.get('win_rate', 0) * 100
        wins = pnl_data.get('wins', 0)
        losses = pnl_data.get('losses', 0)
        total_trades = pnl_data.get('total_trades', 0)
        performance_tier = pnl_data.get('performance_tier', 'N/A')

        # Win rate bar
        win_bar_length = int(win_rate / 100 * 40)
        loss_bar_length = 40 - win_bar_length

        win_bar = self.colorize('█' * win_bar_length, 'green')
        loss_bar = self.colorize('█' * loss_bar_length, 'red')

        lines.append(f"\nWin Rate: {win_rate:.1f}%")
        lines.append(f"[{win_bar}{loss_bar}]")
        lines.append(f"Wins: {wins} | Losses: {losses} | Total: {total_trades}")

        lines.append(f"\nPerformance Tier: {self.colorize(performance_tier, 'cyan')}")

        if 'total_profit_sol' in pnl_data:
            profit = pnl_data['total_profit_sol']
            profit_str = f"{profit:+.4f} SOL"
            profit_color = 'green' if profit > 0 else 'red'
            lines.append(f"Total P&L: {self.colorize(profit_str, profit_color)}")

        lines.append(f"{'='*70}")

        return '\n'.join(lines)

    def create_score_gauge(
        self,
        score: float,
        max_score: float = 100,
        label: str = "Score"
    ) -> str:
        """
        Create gauge visualization for scores.

        Args:
            score: Current score value
            max_score: Maximum possible score
            label: Label for the score

        Returns:
            Formatted ASCII gauge
        """
        percentage = (score / max_score) * 100 if max_score > 0 else 0
        bar_length = int(percentage / 100 * 40)
        bar = '█' * bar_length + '░' * (40 - bar_length)

        # Color based on percentage
        if percentage >= 75:
            bar = self.colorize(bar, 'green')
            level = 'EXCELLENT'
        elif percentage >= 60:
            bar = self.colorize(bar, 'cyan')
            level = 'GOOD'
        elif percentage >= 40:
            bar = self.colorize(bar, 'yellow')
            level = 'MODERATE'
        else:
            bar = self.colorize(bar, 'red')
            level = 'LOW'

        return f"{label}: [{bar}] {score:.1f}/{max_score} ({level})"

    def create_risk_indicator(
        self,
        risk_score: float,
        risk_level: str
    ) -> str:
        """
        Create risk level indicator.

        Args:
            risk_score: Risk score (0-100)
            risk_level: Risk level classification

        Returns:
            Formatted risk indicator
        """
        # Risk gauge (inverted - lower is better)
        bar_length = int(risk_score / 100 * 40)
        bar = '█' * bar_length + '░' * (40 - bar_length)

        # Color based on risk level
        if risk_level == 'HIGH':
            bar = self.colorize(bar, 'red')
            icon = '🚨'
        elif risk_level == 'MEDIUM':
            bar = self.colorize(bar, 'yellow')
            icon = '⚠️ '
        else:
            bar = self.colorize(bar, 'green')
            icon = '✅'

        level_colored = self.colorize(risk_level,
                                      'red' if risk_level == 'HIGH' else
                                      'yellow' if risk_level == 'MEDIUM' else 'green')

        return f"{icon} Risk: [{bar}] {risk_score:.0f}/100 ({level_colored})"

    def create_summary_dashboard(
        self,
        analysis_results: Dict
    ) -> str:
        """
        Create comprehensive summary dashboard.

        Args:
            analysis_results: Complete analysis results

        Returns:
            Formatted ASCII dashboard
        """
        lines = []
        lines.append(f"\n{'#'*70}")
        lines.append(f"{'#' + ' '*68 + '#'}")
        lines.append(f"#{'SOLANA WALLET TRACKER - ANALYSIS DASHBOARD'.center(68)}#")
        lines.append(f"{'#' + ' '*68 + '#'}")
        lines.append(f"{'#'*70}")

        # Key metrics section
        if 'wallet_analysis' in analysis_results:
            wallet = analysis_results['wallet_analysis']
            balance = wallet.get('balance', {})

            lines.append(f"\n📊 KEY METRICS:")
            lines.append(f"   Balance: {balance.get('formatted', 'N/A')}")
            lines.append(f"   Total Transactions: {wallet.get('total_transactions', 0):,}")
            lines.append(f"   Success Rate: {wallet.get('successful_transactions', 0) / max(wallet.get('processed_transactions', 1), 1) * 100:.1f}%")

        # Performance score
        if 'performance_score' in analysis_results:
            score = analysis_results['performance_score']
            lines.append(f"\n{self.create_score_gauge(score['total_score'], 100, 'Performance Score')}")
            lines.append(f"   Tier: {self.colorize(score['tier'], 'cyan')}")

        # Risk indicator
        if 'wallet_risk' in analysis_results:
            risk = analysis_results['wallet_risk']
            lines.append(f"\n{self.create_risk_indicator(risk['risk_score'], risk['risk_level'])}")

        lines.append(f"\n{'#'*70}")

        return '\n'.join(lines)
