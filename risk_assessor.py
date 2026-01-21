"""
Risk Assessment Module
Evaluates wallet and token risks including rug-pull indicators
"""

from typing import Dict, List, Any, Optional
import config
from utils import get_risk_level

class RiskAssessor:
    """
    Comprehensive risk evaluation for wallets and tokens.
    Detects rug-pull indicators, concentration risks, and anomalous behavior.
    """

    def __init__(self):
        self.risk_weights = config.RISK_WEIGHTS
        self.risk_factors = []

    def assess_token_risk(
        self,
        token_info: Optional[Dict],
        holder_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Assess risk for a specific token.

        Args:
            token_info: Token/pair information from DEX
            holder_data: Optional holder distribution data

        Returns:
            Dict with risk score and factors
        """
        risk_score = 0
        risk_factors = []

        if not token_info:
            return {
                'risk_score': 50,
                'risk_level': 'MEDIUM',
                'factors': ['INSUFFICIENT_DATA'],
                'assessment': 'Unable to assess - limited data available'
            }

        # Liquidity risk (0-30 points)
        liquidity = token_info.get('liquidity', {}).get('usd', 0)

        if liquidity < 5000:
            risk_score += 30
            risk_factors.append('VERY_LOW_LIQUIDITY: High rug risk (<$5K)')
        elif liquidity < 20000:
            risk_score += 20
            risk_factors.append('LOW_LIQUIDITY: Significant risk (<$20K)')
        elif liquidity < 100000:
            risk_score += 10
            risk_factors.append('MODERATE_LIQUIDITY: Some risk (<$100K)')
        else:
            risk_factors.append('ADEQUATE_LIQUIDITY: Lower risk (>$100K)')

        # Volume analysis (0-20 points)
        volume_24h = token_info.get('volume', {}).get('h24', 0)

        if liquidity > 0:
            volume_to_liquidity = volume_24h / liquidity if liquidity > 0 else 0

            if volume_to_liquidity < 0.1:
                risk_score += 20
                risk_factors.append('LOW_VOLUME: Minimal trading activity')
            elif volume_to_liquidity > 10:
                risk_score += 15
                risk_factors.append('EXCESSIVE_VOLUME: Possible manipulation')
            else:
                risk_factors.append('NORMAL_VOLUME: Healthy trading activity')

        # Price change analysis (0-20 points)
        price_change_24h = token_info.get('priceChange', {}).get('h24', 0)

        if abs(price_change_24h) > 300:
            risk_score += 20
            risk_factors.append('EXTREME_VOLATILITY: >300% 24h change')
        elif abs(price_change_24h) > 100:
            risk_score += 15
            risk_factors.append('HIGH_VOLATILITY: >100% 24h change')
        elif abs(price_change_24h) > 50:
            risk_score += 10
            risk_factors.append('MODERATE_VOLATILITY: >50% 24h change')

        # Holder concentration (0-30 points) - if available
        if holder_data:
            top_holder_pct = holder_data.get('top_holder_percentage', 0)
            high_risk_threshold = config.ANALYSIS_CONFIG['high_risk_dev_holding_pct']

            if top_holder_pct > high_risk_threshold * 2:
                risk_score += 30
                risk_factors.append(f'EXTREME_CONCENTRATION: Top holder owns >{top_holder_pct:.0f}%')
            elif top_holder_pct > high_risk_threshold:
                risk_score += 20
                risk_factors.append(f'HIGH_CONCENTRATION: Top holder owns >{top_holder_pct:.0f}%')
            else:
                risk_factors.append('BALANCED_DISTRIBUTION: Decentralized holdings')

        # Get risk level
        risk_level, color = get_risk_level(risk_score)

        # Generate assessment
        if risk_score >= 70:
            assessment = 'CRITICAL: Multiple high-risk factors detected'
        elif risk_score >= 50:
            assessment = 'HIGH: Significant risks present, extreme caution advised'
        elif risk_score >= 30:
            assessment = 'MODERATE: Some risk factors, proceed with caution'
        else:
            assessment = 'LOW: Relatively stable metrics, standard risks apply'

        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'factors': risk_factors,
            'assessment': assessment,
            'color': color
        }

    def assess_wallet_risk(
        self,
        wallet_analysis: Dict,
        anomalies: List[Dict]
    ) -> Dict[str, Any]:
        """
        Assess risk indicators for a wallet's behavior.

        Args:
            wallet_analysis: Wallet analysis data
            anomalies: List of detected anomalies

        Returns:
            Dict with wallet risk assessment
        """
        risk_score = 0
        risk_factors = []

        # Anomaly score (0-40 points)
        anomaly_count = len(anomalies)

        if anomaly_count > 5:
            risk_score += 40
            risk_factors.append(f'MULTIPLE_ANOMALIES: {anomaly_count} suspicious patterns')
        elif anomaly_count > 2:
            risk_score += 25
            risk_factors.append(f'SOME_ANOMALIES: {anomaly_count} unusual patterns')
        elif anomaly_count > 0:
            risk_score += 10
            risk_factors.append(f'MINOR_ANOMALIES: {anomaly_count} patterns flagged')

        # Check for high-severity anomalies
        high_severity = [a for a in anomalies if a.get('severity') == 'HIGH']
        if high_severity:
            risk_score += 20
            risk_factors.append(f'HIGH_SEVERITY_ISSUES: {len(high_severity)} critical anomalies')

        # Transaction failure rate (0-30 points)
        total_txs = wallet_analysis.get('total_transactions', 0)
        successful_txs = wallet_analysis.get('successful_transactions', 0)

        if total_txs > 0:
            failure_rate = 1 - (successful_txs / total_txs)

            if failure_rate > 0.3:
                risk_score += 30
                risk_factors.append(f'HIGH_FAILURE_RATE: {failure_rate*100:.1f}% failed txs')
            elif failure_rate > 0.15:
                risk_score += 15
                risk_factors.append(f'MODERATE_FAILURE_RATE: {failure_rate*100:.1f}% failed txs')

        # Balance risk (0-20 points)
        balance_sol = wallet_analysis.get('balance', {}).get('sol', 0)

        if balance_sol < 0.05:
            risk_score += 20
            risk_factors.append('DUST_WALLET: Very low balance (<0.05 SOL)')
        elif balance_sol < 0.5:
            risk_score += 10
            risk_factors.append('LOW_BALANCE: Small wallet (<0.5 SOL)')

        # Recent activity (0-10 points)
        # If we have transaction data, check recency
        parsed_txs = wallet_analysis.get('parsed_transactions', [])
        if parsed_txs:
            import time
            latest_tx = max(tx.get('timestamp', 0) for tx in parsed_txs if tx.get('timestamp'))
            age_days = (time.time() - latest_tx) / 86400

            if age_days > 30:
                risk_score += 10
                risk_factors.append(f'INACTIVE: No activity for {age_days:.0f} days')

        # Get risk level
        risk_level, color = get_risk_level(risk_score)

        if risk_score >= 70:
            assessment = 'HIGH RISK: Multiple red flags, avoid interaction'
        elif risk_score >= 40:
            assessment = 'MODERATE RISK: Exercise caution, verify independently'
        else:
            assessment = 'LOW RISK: Standard security practices apply'

        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'factors': risk_factors,
            'assessment': assessment,
            'color': color,
            'anomaly_count': anomaly_count
        }

    def detect_rug_pull_indicators(
        self,
        token_info: Optional[Dict],
        transactions: List[Dict]
    ) -> List[Dict]:
        """
        Detect specific rug-pull indicators.

        Returns:
            List of detected rug-pull warning signs
        """
        indicators = []

        if not token_info:
            return indicators

        # 1. Liquidity removed or very low
        liquidity = token_info.get('liquidity', {}).get('usd', 0)
        if liquidity < 1000:
            indicators.append({
                'type': 'LIQUIDITY_DRAIN',
                'severity': 'CRITICAL',
                'description': 'Liquidity critically low or removed',
                'value': f'${liquidity:,.0f}'
            })

        # 2. Extreme price dump
        price_change_24h = token_info.get('priceChange', {}).get('h24', 0)
        if price_change_24h < -80:
            indicators.append({
                'type': 'PRICE_COLLAPSE',
                'severity': 'CRITICAL',
                'description': 'Severe price dump detected',
                'value': f'{price_change_24h:.1f}%'
            })

        # 3. Volume spike with price dump (dump & pump pattern)
        volume_24h = token_info.get('volume', {}).get('h24', 0)
        if liquidity > 0:
            volume_ratio = volume_24h / liquidity
            if volume_ratio > 5 and price_change_24h < -30:
                indicators.append({
                    'type': 'DUMP_PATTERN',
                    'severity': 'HIGH',
                    'description': 'High volume with price dump',
                    'value': f'{volume_ratio:.1f}x liquidity'
                })

        # 4. Analyze transaction patterns for suspicious activity
        if transactions:
            # Check for large sudden outflows
            large_outflows = []
            for tx in transactions[-20:]:  # Last 20 transactions
                transfers = tx.get('pre_balances', [])
                if transfers:
                    # Look for significant balance drops
                    pre = sum(tx.get('pre_balances', []))
                    post = sum(tx.get('post_balances', []))
                    if pre > 0:
                        drop_pct = (pre - post) / pre * 100
                        if drop_pct > 50:
                            large_outflows.append(drop_pct)

            if len(large_outflows) > 3:
                indicators.append({
                    'type': 'MASS_EXODUS',
                    'severity': 'HIGH',
                    'description': 'Multiple large withdrawals detected',
                    'value': f'{len(large_outflows)} major outflows'
                })

        return indicators

    def generate_risk_report(
        self,
        wallet_risk: Dict,
        token_risks: List[Dict],
        rug_indicators: List[Dict]
    ) -> str:
        """
        Generate comprehensive risk assessment report.

        Returns:
            Formatted text report
        """
        lines = []
        lines.append(f"\n{'='*70}")
        lines.append(f"⚠️  RISK ASSESSMENT REPORT")
        lines.append(f"{'='*70}")

        # Wallet risk
        lines.append(f"\n🔐 WALLET RISK ANALYSIS:")
        lines.append(f"   Risk Score: {wallet_risk['risk_score']}/100 ({wallet_risk['risk_level']})")
        lines.append(f"   Assessment: {wallet_risk['assessment']}")

        if wallet_risk.get('factors'):
            lines.append(f"\n   Risk Factors:")
            for factor in wallet_risk['factors']:
                lines.append(f"      • {factor}")

        # Token risks (if any)
        if token_risks:
            lines.append(f"\n💎 TOKEN RISK ANALYSIS:")
            for i, token_risk in enumerate(token_risks[:3], 1):
                lines.append(f"\n   Token #{i}:")
                lines.append(f"      Risk Score: {token_risk['risk_score']}/100 ({token_risk['risk_level']})")
                lines.append(f"      Assessment: {token_risk['assessment']}")

                if token_risk.get('factors'):
                    lines.append(f"      Factors:")
                    for factor in token_risk['factors'][:3]:
                        lines.append(f"         • {factor}")

        # Rug-pull indicators (critical)
        if rug_indicators:
            lines.append(f"\n🚨 RUG-PULL WARNING INDICATORS:")
            for indicator in rug_indicators:
                severity = indicator['severity']
                lines.append(
                    f"   [{severity}] {indicator['type']}: "
                    f"{indicator['description']} ({indicator['value']})"
                )

        # Overall recommendation
        lines.append(f"\n{'='*70}")
        lines.append(f"RISK MANAGEMENT RECOMMENDATIONS:")
        lines.append(f"• Always DYOR (Do Your Own Research)")
        lines.append(f"• Never invest more than you can afford to lose")
        lines.append(f"• Use stop-losses: -10-20% for high-risk plays")
        lines.append(f"• Diversify: Limit single position to 1-5% of portfolio")
        lines.append(f"• Verify token contracts and liquidity locks independently")
        lines.append(f"{'='*70}")

        return '\n'.join(lines)

    def calculate_composite_risk(
        self,
        wallet_risk: Dict,
        token_risks: List[Dict],
        rug_indicators: List[Dict]
    ) -> Dict[str, Any]:
        """
        Calculate composite risk score across all factors.

        Returns:
            Dict with overall risk assessment
        """
        # Weight the scores
        wallet_weight = 0.4
        token_weight = 0.5
        rug_weight = 0.1

        wallet_score = wallet_risk.get('risk_score', 0)

        # Average token risk if multiple tokens
        if token_risks:
            avg_token_score = sum(t['risk_score'] for t in token_risks) / len(token_risks)
        else:
            avg_token_score = 0

        # Rug indicator penalty
        rug_penalty = len(rug_indicators) * 15  # 15 points per indicator

        # Calculate composite
        composite_score = (
            wallet_score * wallet_weight +
            avg_token_score * token_weight +
            rug_penalty * rug_weight
        )

        composite_score = min(composite_score, 100)  # Cap at 100

        risk_level, color = get_risk_level(composite_score)

        return {
            'composite_score': composite_score,
            'risk_level': risk_level,
            'wallet_score': wallet_score,
            'avg_token_score': avg_token_score,
            'rug_indicator_count': len(rug_indicators),
            'color': color
        }
