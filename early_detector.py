"""
Early Token Detection Module
Identifies early token entries and emerging opportunities
"""

from typing import Dict, List, Any, Optional
import time
from datetime import datetime, timezone
import config
from utils import fetch_json, retry_with_backoff, RateLimiter

class EarlyTokenDetector:
    """
    Detects early token purchases and emerging token opportunities.
    Uses DexScreener and transaction timing analysis.
    """

    def __init__(self):
        self.dex_api = config.DEX_APIS['dexscreener']
        self.rate_limiter = RateLimiter(calls_per_second=5)
        self.detected_tokens = []

    @retry_with_backoff(max_retries=3)
    def get_token_info(self, token_address: str) -> Optional[Dict]:
        """
        Fetch token information from DexScreener.

        Returns:
            Dict with token pair data or None
        """
        self.rate_limiter.wait()

        url = f"{self.dex_api['base_url']}{self.dex_api['endpoints']['pairs_by_token']}".format(
            address=token_address
        )

        try:
            data = fetch_json(url)
            if data and 'pairs' in data and data['pairs']:
                return data['pairs'][0]  # Return first pair
        except Exception as e:
            print(f"⚠️  Could not fetch token info: {str(e)[:80]}")

        return None

    def detect_early_entries(
        self,
        transactions: List[Dict],
        early_window: int = None
    ) -> List[Dict]:
        """
        Detect potential early token entries from transaction history.

        Args:
            transactions: List of parsed transactions
            early_window: Time window in seconds to consider "early" (default: 300s = 5min)

        Returns:
            List of early entry signals
        """
        if early_window is None:
            early_window = config.ANALYSIS_CONFIG['early_detection_window']

        print(f"\n🔍 Detecting early token entries (within {early_window}s of launch)...")

        early_entries = []
        token_first_seen = {}

        # Sort transactions by timestamp
        sorted_txs = sorted(
            transactions,
            key=lambda x: x.get('timestamp', 0)
        )

        for tx in sorted_txs:
            if not tx.get('success', False):
                continue

            timestamp = tx.get('timestamp', 0)
            accounts = tx.get('accounts', [])

            # Look for token program interactions
            programs = tx.get('programs', [])
            has_token_program = any(
                'Token' in prog or 'token' in prog.lower()
                for prog in programs
            )

            if has_token_program:
                # Track first interaction with each token account
                for account in accounts:
                    if account not in token_first_seen:
                        token_first_seen[account] = timestamp

                    # Check if this is within early window
                    first_seen = token_first_seen[account]
                    time_delta = timestamp - first_seen

                    if 0 < time_delta <= early_window:
                        # Potential early entry
                        early_entries.append({
                            'token_account': account,
                            'entry_timestamp': timestamp,
                            'time_from_first_seen': time_delta,
                            'transaction': tx.get('signature', 'Unknown'),
                            'programs_used': programs
                        })

        # Deduplicate by token account
        unique_entries = {}
        for entry in early_entries:
            token = entry['token_account']
            if token not in unique_entries:
                unique_entries[token] = entry

        early_list = list(unique_entries.values())

        print(f"✅ Found {len(early_list)} potential early entries")

        return early_list

    def analyze_token_launch_timing(
        self,
        token_address: str,
        first_interaction_time: int
    ) -> Dict[str, Any]:
        """
        Analyze timing relative to token launch.

        Returns:
            Dict with launch timing analysis
        """
        # Try to get token creation time from DexScreener
        token_info = self.get_token_info(token_address)

        if not token_info:
            return {
                'launch_detected': False,
                'entry_timing': 'UNKNOWN'
            }

        # Extract launch time from pair creation
        pair_created_at = token_info.get('pairCreatedAt', 0)

        if pair_created_at:
            time_delta = first_interaction_time - (pair_created_at / 1000)  # Convert ms to s

            if time_delta < 0:
                timing = 'PRE_LAUNCH'  # Transaction before recorded launch
            elif time_delta < 300:
                timing = 'VERY_EARLY'  # Within 5 minutes
            elif time_delta < 3600:
                timing = 'EARLY'  # Within 1 hour
            elif time_delta < 86400:
                timing = 'DAY_ONE'  # Within 24 hours
            else:
                timing = 'LATE'

            return {
                'launch_detected': True,
                'pair_created_at': pair_created_at,
                'entry_time_delta': time_delta,
                'entry_timing': timing,
                'liquidity_usd': token_info.get('liquidity', {}).get('usd', 0),
                'volume_24h': token_info.get('volume', {}).get('h24', 0)
            }

        return {'launch_detected': False}

    def score_early_opportunity(
        self,
        entry_data: Dict,
        token_info: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Score an early entry opportunity based on various factors.

        Returns:
            Dict with opportunity score and assessment
        """
        score = 0
        factors = []

        # Timing score (0-40 points)
        time_delta = entry_data.get('time_from_first_seen', 0)
        if time_delta < 60:
            score += 40
            factors.append("ULTRA_EARLY: <1 min from detection")
        elif time_delta < 300:
            score += 30
            factors.append("VERY_EARLY: <5 min from detection")
        elif time_delta < 600:
            score += 20
            factors.append("EARLY: <10 min from detection")
        else:
            score += 10
            factors.append("MODERATE: >10 min from detection")

        # Token info score (0-60 points) - if available
        if token_info:
            liquidity = token_info.get('liquidity', {}).get('usd', 0)
            volume = token_info.get('volume', {}).get('h24', 0)

            # Liquidity score (0-30)
            if 10000 <= liquidity <= 100000:
                score += 30
                factors.append("OPTIMAL_LIQUIDITY: $10K-$100K")
            elif 5000 <= liquidity < 10000:
                score += 20
                factors.append("LOW_LIQUIDITY: $5K-$10K")
            elif liquidity > 100000:
                score += 15
                factors.append("HIGH_LIQUIDITY: >$100K")
            else:
                score += 5
                factors.append("VERY_LOW_LIQUIDITY: <$5K")

            # Volume score (0-30)
            if volume > 50000:
                score += 30
                factors.append("HIGH_VOLUME: >$50K/24h")
            elif volume > 10000:
                score += 20
                factors.append("MODERATE_VOLUME: $10K-$50K/24h")
            elif volume > 1000:
                score += 10
                factors.append("LOW_VOLUME: $1K-$10K/24h")
            else:
                score += 5
                factors.append("MINIMAL_VOLUME: <$1K/24h")

        # Classify opportunity
        if score >= 80:
            opportunity = "HIGH"
            recommendation = "Strong early entry signal"
        elif score >= 60:
            opportunity = "MODERATE"
            recommendation = "Interesting opportunity, proceed with caution"
        elif score >= 40:
            opportunity = "LOW"
            recommendation = "Weak signal, high risk"
        else:
            opportunity = "MINIMAL"
            recommendation = "Not recommended"

        return {
            'score': score,
            'opportunity_level': opportunity,
            'recommendation': recommendation,
            'factors': factors
        }

    def find_emerging_tokens(
        self,
        transactions: List[Dict]
    ) -> List[Dict]:
        """
        Find emerging tokens from recent wallet activity.
        Combines early detection with volume/activity analysis.

        Returns:
            List of emerging token opportunities
        """
        print(f"\n🚀 Searching for emerging token opportunities...")

        # Get early entries
        early_entries = self.detect_early_entries(transactions)

        emerging_tokens = []

        for entry in early_entries[:10]:  # Limit API calls
            token_address = entry['token_account']

            # Get token info
            token_info = self.get_token_info(token_address)

            # Score opportunity
            score_data = self.score_early_opportunity(entry, token_info)

            emerging_tokens.append({
                'token_address': token_address,
                'entry_data': entry,
                'token_info': token_info,
                'opportunity_score': score_data,
                'timestamp': entry['entry_timestamp']
            })

        # Sort by opportunity score
        emerging_tokens = sorted(
            emerging_tokens,
            key=lambda x: x['opportunity_score']['score'],
            reverse=True
        )

        if emerging_tokens:
            print(f"✅ Identified {len(emerging_tokens)} emerging tokens")
            top_score = emerging_tokens[0]['opportunity_score']['score']
            print(f"   Top opportunity score: {top_score}/100")
        else:
            print(f"ℹ️  No emerging tokens detected in recent activity")

        return emerging_tokens

    def generate_early_detection_report(
        self,
        emerging_tokens: List[Dict]
    ) -> str:
        """
        Generate formatted report of early token detections.

        Returns:
            Formatted text report
        """
        if not emerging_tokens:
            return "\nℹ️  No early token entries detected in analyzed period."

        lines = []
        lines.append(f"\n{'='*70}")
        lines.append(f"🚀 EARLY TOKEN DETECTION REPORT")
        lines.append(f"{'='*70}")

        for i, token in enumerate(emerging_tokens[:5], 1):
            score = token['opportunity_score']
            entry = token['entry_data']
            info = token['token_info']

            lines.append(f"\n#{i} | Score: {score['score']}/100 ({score['opportunity_level']})")
            lines.append(f"   Token: {token['token_address'][:16]}...")
            lines.append(f"   Entry Time: {entry['time_from_first_seen']}s from first detection")

            if info:
                liquidity = info.get('liquidity', {}).get('usd', 0)
                volume = info.get('volume', {}).get('h24', 0)
                lines.append(f"   Liquidity: ${liquidity:,.0f}")
                lines.append(f"   Volume (24h): ${volume:,.0f}")

            lines.append(f"   Assessment: {score['recommendation']}")

            # Key factors
            if score['factors']:
                lines.append(f"   Factors:")
                for factor in score['factors'][:3]:
                    lines.append(f"      • {factor}")

        lines.append(f"\n{'='*70}")
        lines.append("⚠️  REMEMBER: Early entries carry HIGH RISK. DYOR and manage position size.")
        lines.append(f"{'='*70}")

        return '\n'.join(lines)
