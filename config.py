"""
Configuration for Solana Wallet Tracker
Free/Public API endpoints and settings (2026 Edition)
"""

# Solana RPC Endpoints (Free Tiers) - Multi-provider failover
RPC_ENDPOINTS = [
    {
        "name": "Helius",
        "url": "https://rpc.helius.xyz",
        "rate_limit": 10,  # RPS
        "priority": 1
    },
    {
        "name": "Public Solana",
        "url": "https://api.mainnet-beta.solana.com",
        "rate_limit": 5,
        "priority": 2
    },
    {
        "name": "Chainstack",
        "url": "https://solana-mainnet.core.chainstack.com",
        "rate_limit": 10,
        "priority": 3
    }
]

# Explorer APIs (Free Tiers)
EXPLORER_APIS = {
    "solscan": {
        "base_url": "https://public-api.solscan.io",
        "rate_limit": 10,
        "endpoints": {
            "account_txs": "/account/transactions",
            "account_tokens": "/account/tokens",
            "token_holders": "/token/holders"
        }
    },
    "orb": {
        "base_url": "https://api.helius.xyz",
        "endpoints": {
            "tx_history": "/v0/addresses/{address}/transactions",
            "parsed_txs": "/v0/transactions"
        }
    }
}

# DEX & Token Analytics
DEX_APIS = {
    "dexscreener": {
        "base_url": "https://api.dexscreener.com/latest",
        "endpoints": {
            "pairs_by_token": "/dex/tokens/{address}",
            "pairs_by_chain": "/dex/pairs/solana/{pair_address}",
            "search": "/dex/search"
        }
    },
    "hellomoon": {
        "base_url": "https://rest-api.hellomoon.io",
        "endpoints": {
            "token_holders": "/v0/token/holders",
            "token_info": "/v0/token/info"
        }
    }
}

# Analytics Platforms
ANALYTICS_APIS = {
    "coingecko": {
        "base_url": "https://api.coingecko.com/api/v3",
        "endpoints": {
            "price": "/simple/price",
            "history": "/coins/{id}/market_chart"
        }
    }
}

# Analysis Parameters
ANALYSIS_CONFIG = {
    "tx_batch_size": 20,
    "max_tx_history": 10000,
    "cache_duration": 900,  # 15 minutes
    "early_detection_window": 300,  # 5 minutes from launch
    "min_holders_for_early": 50,
    "cluster_min_shared_txs": 5,
    "whale_threshold_sol": 50000,
    "large_trade_threshold": 10000,
    "pattern_burst_threshold": 10,  # txs per hour
    "high_risk_dev_holding_pct": 20,
    "pnl_win_threshold": 0.75  # 75% win rate
}

# Risk Scoring Weights
RISK_WEIGHTS = {
    "dev_holdings": 0.3,
    "liquidity_lock": 0.25,
    "holder_concentration": 0.2,
    "volume_anomaly": 0.15,
    "wash_trading": 0.1
}

# Visualization Settings
VIZ_CONFIG = {
    "heatmap_bins": 24,  # hourly
    "flow_graph_max_nodes": 50,
    "color_scheme": "viridis"
}

# Disclaimer Text
DISCLAIMER = """
╔══════════════════════════════════════════════════════════════════╗
║                     IMPORTANT DISCLAIMER                         ║
╠══════════════════════════════════════════════════════════════════╣
║ This tool provides analytical research from PUBLIC blockchain    ║
║ data only. Markets are highly volatile and unpredictable.        ║
║                                                                  ║
║ • NO profit guarantees or investment advice provided             ║
║ • Crypto involves risk of TOTAL LOSS                            ║
║ • DYOR (Do Your Own Research) - Always verify independently     ║
║ • Past performance does NOT predict future results              ║
║ • Only risk capital you can afford to lose (1-5% per trade)    ║
║ • This is educational analysis, not financial advice            ║
║                                                                  ║
║ Use responsibly. Trade at your own risk.                        ║
╚══════════════════════════════════════════════════════════════════╝
"""
