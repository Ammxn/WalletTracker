"""
Utility functions for Solana Wallet Tracker
"""

import re
import time
import requests
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
from functools import wraps
import config

def is_valid_solana_address(address: str) -> bool:
    """
    Validate Solana wallet address using Base58 regex.
    Pattern: ^[1-9A-HJ-NP-Za-km-z]{32,44}$
    """
    pattern = r'^[1-9A-HJ-NP-Za-km-z]{32,44}$'
    return bool(re.match(pattern, address))

def extract_addresses(text: str) -> List[str]:
    """Extract all valid Solana addresses from text."""
    pattern = r'\b[1-9A-HJ-NP-Za-km-z]{32,44}\b'
    potential_addresses = re.findall(pattern, text)
    return [addr for addr in potential_addresses if is_valid_solana_address(addr)]

def retry_with_backoff(max_retries: int = 4, base_delay: float = 2.0):
    """
    Decorator for exponential backoff retry logic.
    Retries up to max_retries times with delays: 2s, 4s, 8s, 16s
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        raise
                    delay = base_delay * (2 ** attempt)
                    print(f"⚠️  Attempt {attempt + 1} failed: {str(e)[:100]}. Retrying in {delay}s...")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, calls_per_second: int):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0

    def wait(self):
        """Wait if necessary to respect rate limit."""
        elapsed = time.time() - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()

def format_sol_amount(lamports: int) -> str:
    """Convert lamports to SOL with formatting."""
    sol = lamports / 1e9
    if sol >= 1000000:
        return f"{sol/1e6:.2f}M SOL"
    elif sol >= 1000:
        return f"{sol/1e3:.2f}K SOL"
    else:
        return f"{sol:.4f} SOL"

def format_usd_amount(amount: float) -> str:
    """Format USD amount with appropriate suffix."""
    if amount >= 1000000:
        return f"${amount/1e6:.2f}M"
    elif amount >= 1000:
        return f"${amount/1e3:.2f}K"
    else:
        return f"${amount:.2f}"

def format_timestamp(timestamp: int) -> str:
    """Format Unix timestamp to readable datetime."""
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")

def calculate_pnl(
    buy_price: float,
    sell_price: float,
    amount: float
) -> Dict[str, float]:
    """
    Calculate PnL metrics for a trade.

    Returns:
        Dict with 'profit', 'roi_pct', 'win' keys
    """
    profit = (sell_price - buy_price) * amount
    roi_pct = ((sell_price - buy_price) / buy_price * 100) if buy_price > 0 else 0

    return {
        "profit": profit,
        "roi_pct": roi_pct,
        "win": profit > 0
    }

def aggregate_pnl(trades: List[Dict]) -> Dict[str, Any]:
    """
    Aggregate PnL statistics from multiple trades.

    Returns:
        Dict with total_profit, win_rate, avg_roi, etc.
    """
    if not trades:
        return {
            "total_profit": 0,
            "win_rate": 0,
            "avg_roi": 0,
            "total_trades": 0,
            "wins": 0,
            "losses": 0
        }

    total_profit = sum(t.get('profit', 0) for t in trades)
    wins = [t for t in trades if t.get('win', False)]
    win_rate = len(wins) / len(trades) if trades else 0
    avg_roi = sum(t.get('roi_pct', 0) for t in trades) / len(trades) if trades else 0

    return {
        "total_profit": total_profit,
        "win_rate": win_rate,
        "avg_roi": avg_roi,
        "total_trades": len(trades),
        "wins": len(wins),
        "losses": len(trades) - len(wins)
    }

def get_risk_level(score: float) -> tuple:
    """
    Convert risk score (0-100) to level and color.

    Returns:
        Tuple of (level_str, color_code)
    """
    if score >= 70:
        return ("HIGH", "red")
    elif score >= 40:
        return ("MEDIUM", "yellow")
    else:
        return ("LOW", "green")

@retry_with_backoff(max_retries=4)
def fetch_json(url: str, headers: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
    """
    Fetch JSON data from URL with retry logic.
    """
    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

def truncate_address(address: str, start: int = 4, end: int = 4) -> str:
    """Truncate wallet address for display (e.g., '5Q54...uRGj')."""
    if len(address) <= start + end:
        return address
    return f"{address[:start]}...{address[-end:]}"

def create_progress_bar(current: int, total: int, width: int = 40) -> str:
    """Create a text-based progress bar."""
    if total == 0:
        return "[" + "=" * width + "]"

    filled = int(width * current / total)
    bar = "=" * filled + "-" * (width - filled)
    percentage = current / total * 100

    return f"[{bar}] {percentage:.1f}% ({current}/{total})"

def detect_pattern_type(tx_data: List[Dict]) -> str:
    """
    Detect transaction pattern type from batch of transactions.

    Returns:
        Pattern classification string
    """
    if not tx_data:
        return "UNKNOWN"

    # Count transaction types
    swaps = sum(1 for tx in tx_data if 'swap' in str(tx).lower())
    transfers = sum(1 for tx in tx_data if 'transfer' in str(tx).lower())

    if swaps > len(tx_data) * 0.6:
        return "HEAVY_TRADING"
    elif transfers > len(tx_data) * 0.7:
        return "DISTRIBUTION"
    elif len(tx_data) > 10 and all(
        abs(tx_data[i].get('timestamp', 0) - tx_data[i-1].get('timestamp', 0)) < 60
        for i in range(1, min(10, len(tx_data)))
    ):
        return "BURST_ACTIVITY"
    else:
        return "MIXED"

def format_table_data(headers: List[str], rows: List[List[Any]]) -> str:
    """Format data as ASCII table."""
    from tabulate import tabulate
    return tabulate(rows, headers=headers, tablefmt="grid")
