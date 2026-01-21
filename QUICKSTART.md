# 🚀 Quick Start Guide

## Get Running in 3 Minutes

### Step 1: Install Dependencies

```bash
pip install solana requests pandas numpy matplotlib networkx rich click tabulate colorama
```

Or use the requirements file:

```bash
pip install -r requirements.txt
```

### Step 2: Test the Installation

```bash
python tracker.py --help
```

You should see the help message with usage instructions.

### Step 3: Analyze Your First Wallet

Replace `<WALLET_ADDRESS>` with any Solana wallet address:

```bash
python tracker.py <WALLET_ADDRESS>
```

**Example with a real wallet:**

```bash
# Analyze Jupiter Aggregator wallet
python tracker.py JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4
```

---

## Common Issues

### 1. "No module named 'solana'"

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. "Rate limit exceeded"

**Solution**: The tool automatically handles rate limits with exponential backoff. If you're hitting limits, wait a minute and try again.

### 3. "Invalid Solana address"

**Solution**: Ensure the address is a valid Base58-encoded Solana address (32-44 characters, no 0, O, I, or l).

### 4. "Connection timeout"

**Solution**: Check your internet connection. The tool will automatically rotate between multiple RPC providers.

---

## What You'll See

The analysis includes:

1. **Balance & Transaction Count**
2. **Flow Analysis** - Where SOL is going/coming from
3. **Pattern Detection** - Clusters, timing, PnL
4. **Early Token Signals** - Emerging opportunities
5. **Risk Assessment** - Red flags and indicators
6. **Strategic Insights** - Educational observations

---

## Next Steps

1. **Read the README**: Comprehensive documentation in `README.md`
2. **Customize Config**: Edit `config.py` for your RPC endpoints
3. **Build Scripts**: Import modules programmatically
4. **Create Dashboards**: Use results in Streamlit/Dash apps

---

## Need Help?

- Check `README.md` for detailed documentation
- Review code comments in each module
- Open an issue on GitHub

**Happy analyzing! 🎯**
