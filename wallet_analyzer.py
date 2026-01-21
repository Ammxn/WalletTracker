"""
Core Wallet Analyzer Module
Handles RPC connections, transaction fetching, and wallet analysis
"""

import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from solders.pubkey import Pubkey
from solders.signature import Signature
import config
from utils import (
    retry_with_backoff,
    RateLimiter,
    format_sol_amount,
    format_timestamp,
    format_usd_amount
)

class MultiRPCClient:
    """
    Multi-provider RPC client with automatic failover.
    Rotates between providers for reliability.
    """

    def __init__(self):
        self.providers = sorted(
            config.RPC_ENDPOINTS,
            key=lambda x: x['priority']
        )
        self.current_index = 0
        self.clients = {}
        self.rate_limiters = {}

        # Initialize clients and rate limiters
        for provider in self.providers:
            self.clients[provider['name']] = Client(provider['url'])
            self.rate_limiters[provider['name']] = RateLimiter(
                provider['rate_limit']
            )

    def get_client(self) -> tuple:
        """Get current RPC client and its rate limiter."""
        provider = self.providers[self.current_index]
        return (
            self.clients[provider['name']],
            self.rate_limiters[provider['name']],
            provider['name']
        )

    def rotate(self):
        """Rotate to next provider."""
        self.current_index = (self.current_index + 1) % len(self.providers)

    @retry_with_backoff(max_retries=4)
    def call_with_failover(self, method: str, *args, **kwargs):
        """
        Call RPC method with automatic failover.
        Tries all providers before giving up.
        """
        attempts_per_provider = 2
        total_attempts = len(self.providers) * attempts_per_provider

        for attempt in range(total_attempts):
            client, limiter, provider_name = self.get_client()
            limiter.wait()

            try:
                result = getattr(client, method)(*args, **kwargs)
                return result
            except Exception as e:
                print(f"⚠️  {provider_name} failed: {str(e)[:80]}")
                self.rotate()
                if attempt == total_attempts - 1:
                    raise Exception(f"All RPC providers failed for {method}")
                time.sleep(0.5)

class WalletAnalyzer:
    """
    Main wallet analysis engine.
    Fetches and parses transaction data from Solana blockchain.
    """

    def __init__(self):
        self.rpc_client = MultiRPCClient()
        self.cache = {}
        self.cache_timestamps = {}

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached data if not expired."""
        if key in self.cache:
            age = time.time() - self.cache_timestamps.get(key, 0)
            if age < config.ANALYSIS_CONFIG['cache_duration']:
                return self.cache[key]
        return None

    def _set_cached(self, key: str, value: Any):
        """Set cached data with timestamp."""
        self.cache[key] = value
        self.cache_timestamps[key] = time.time()

    def get_transaction_history(
        self,
        address: str,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Fetch transaction history for wallet address.
        Uses pagination to get up to max_tx_history transactions.

        Args:
            address: Solana wallet address
            limit: Number of transactions per batch (max 1000)

        Returns:
            List of transaction signatures with metadata
        """
        cache_key = f"tx_history_{address}_{limit}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        print(f"📡 Fetching transaction history for {address[:8]}...")

        all_signatures = []
        before_sig = None
        max_txs = config.ANALYSIS_CONFIG['max_tx_history']

        # Convert address string to Pubkey object
        pubkey = Pubkey.from_string(address)

        while len(all_signatures) < max_txs:
            try:
                result = self.rpc_client.call_with_failover(
                    'get_signatures_for_address',
                    pubkey,
                    limit=min(limit, max_txs - len(all_signatures)),
                    before=before_sig
                )

                if not result:
                    break

                # Handle both dict response and solders response object
                if hasattr(result, 'value'):
                    signatures = result.value
                elif isinstance(result, dict) and 'result' in result:
                    signatures = result['result']
                else:
                    break
                if not signatures:
                    break

                # Convert signatures to dicts if they're objects
                sig_list = []
                for sig in signatures:
                    if hasattr(sig, 'signature'):
                        sig_dict = {
                            'signature': str(sig.signature),
                            'slot': sig.slot if hasattr(sig, 'slot') else 0,
                            'err': sig.err if hasattr(sig, 'err') else None,
                            'blockTime': sig.block_time if hasattr(sig, 'block_time') else 0
                        }
                        sig_list.append(sig_dict)
                    else:
                        sig_list.append(sig)

                all_signatures.extend(sig_list)
                before_sig = sig_list[-1]['signature'] if sig_list else None

                print(f"   Fetched {len(all_signatures)} transactions...")

                # Break if we got fewer than requested (end of history)
                if len(signatures) < limit:
                    break

            except Exception as e:
                print(f"❌ Error fetching signatures: {str(e)[:100]}")
                break

        print(f"✅ Retrieved {len(all_signatures)} total transactions")
        self._set_cached(cache_key, all_signatures)
        return all_signatures

    def get_transaction_details(
        self,
        signature: str,
        encoding: str = 'jsonParsed'
    ) -> Optional[Dict]:
        """
        Fetch detailed transaction data including routes and inner instructions.

        Args:
            signature: Transaction signature
            encoding: Response encoding (jsonParsed for human-readable)

        Returns:
            Parsed transaction data or None
        """
        cache_key = f"tx_details_{signature}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            # Convert signature string to Signature object
            sig_obj = Signature.from_string(signature)

            result = self.rpc_client.call_with_failover(
                'get_transaction',
                sig_obj,
                encoding=encoding,
                max_supported_transaction_version=0
            )

            if result:
                # Handle both dict response and solders response object
                if hasattr(result, 'value'):
                    tx_data = result.value
                elif isinstance(result, dict) and 'result' in result:
                    tx_data = result['result']
                else:
                    return None

                if tx_data:
                    self._set_cached(cache_key, tx_data)
                    return tx_data

        except Exception as e:
            print(f"⚠️  Error fetching tx {signature[:8]}: {str(e)[:80]}")

        return None

    def parse_transaction(self, tx_data: Dict) -> Dict[str, Any]:
        """
        Parse transaction data to extract meaningful information.

        Returns:
            Dict with parsed transaction details including:
            - timestamp, signature, fee
            - pre/post balances
            - inner instructions (swaps, transfers)
            - program IDs involved
        """
        if not tx_data:
            return {}

        # Handle both dict and solders object
        if hasattr(tx_data, 'block_time'):
            # Solders object
            timestamp = tx_data.block_time if tx_data.block_time else 0
            slot = tx_data.slot if hasattr(tx_data, 'slot') else 0

            meta = tx_data.transaction.meta if hasattr(tx_data, 'transaction') and hasattr(tx_data.transaction, 'meta') else None
            transaction = tx_data.transaction.transaction if hasattr(tx_data, 'transaction') and hasattr(tx_data.transaction, 'transaction') else None

            if not meta or not transaction:
                return {}

            parsed = {
                'signature': str(transaction.signatures[0]) if transaction.signatures else '',
                'timestamp': timestamp,
                'timestamp_str': format_timestamp(timestamp),
                'slot': slot,
                'fee': meta.fee if hasattr(meta, 'fee') else 0,
                'success': not meta.err if hasattr(meta, 'err') else True,
                'pre_balances': list(meta.pre_balances) if hasattr(meta, 'pre_balances') else [],
                'post_balances': list(meta.post_balances) if hasattr(meta, 'post_balances') else [],
                'inner_instructions': [],
                'log_messages': list(meta.log_messages) if hasattr(meta, 'log_messages') else [],
                'accounts': [],
                'programs': []
            }

            # Extract accounts from message
            if hasattr(transaction, 'message') and hasattr(transaction.message, 'account_keys'):
                parsed['accounts'] = [str(key) for key in transaction.message.account_keys]

            # Extract program IDs
            if hasattr(transaction, 'message') and hasattr(transaction.message, 'instructions'):
                for inst in transaction.message.instructions:
                    if hasattr(inst, 'program_id_index'):
                        idx = inst.program_id_index
                        if idx < len(parsed['accounts']):
                            program = parsed['accounts'][idx]
                            if program not in parsed['programs']:
                                parsed['programs'].append(program)
        else:
            # Dict response
            if 'blockTime' not in tx_data:
                return {}

            meta = tx_data.get('meta', {})
            transaction = tx_data.get('transaction', {})

            parsed = {
                'signature': tx_data.get('transaction', {}).get('signatures', [''])[0],
                'timestamp': tx_data.get('blockTime', 0),
                'timestamp_str': format_timestamp(tx_data.get('blockTime', 0)),
                'slot': tx_data.get('slot', 0),
                'fee': meta.get('fee', 0),
                'success': meta.get('err') is None,
                'pre_balances': meta.get('preBalances', []),
                'post_balances': meta.get('postBalances', []),
                'inner_instructions': meta.get('innerInstructions', []),
                'log_messages': meta.get('logMessages', []),
                'accounts': [],
                'programs': []
            }

            # Extract account keys
            message = transaction.get('message', {})
            if 'accountKeys' in message:
                parsed['accounts'] = [
                    acc.get('pubkey', acc) if isinstance(acc, dict) else acc
                    for acc in message['accountKeys']
                ]

            # Extract program IDs from instructions
            instructions = message.get('instructions', [])
            for inst in instructions:
                program_id_index = inst.get('programIdIndex')
                if program_id_index is not None and program_id_index < len(parsed['accounts']):
                    program = parsed['accounts'][program_id_index]
                    if program not in parsed['programs']:
                        parsed['programs'].append(program)

        return parsed

    def get_wallet_balance(self, address: str) -> Dict[str, Any]:
        """
        Get current SOL balance for wallet.

        Returns:
            Dict with lamports and SOL amounts
        """
        try:
            # Convert address string to Pubkey object
            pubkey = Pubkey.from_string(address)

            result = self.rpc_client.call_with_failover(
                'get_balance',
                pubkey
            )

            if result:
                # Handle both dict response and solders response object
                if hasattr(result, 'value'):
                    lamports = result.value
                elif isinstance(result, dict) and 'result' in result:
                    lamports = result['result']['value']
                else:
                    lamports = 0

                return {
                    'lamports': lamports,
                    'sol': lamports / 1e9,
                    'formatted': format_sol_amount(lamports)
                }

        except Exception as e:
            print(f"⚠️  Error fetching balance: {str(e)[:100]}")

        return {'lamports': 0, 'sol': 0, 'formatted': '0 SOL'}

    def batch_process_transactions(
        self,
        signatures: List[Dict],
        batch_size: int = None
    ) -> List[Dict]:
        """
        Process multiple transactions in batches.

        Args:
            signatures: List of signature dicts from get_transaction_history
            batch_size: Number to process per batch

        Returns:
            List of parsed transaction data
        """
        if batch_size is None:
            batch_size = config.ANALYSIS_CONFIG['tx_batch_size']

        parsed_txs = []
        total = len(signatures)

        print(f"\n🔍 Processing {total} transactions in batches of {batch_size}...")

        for i in range(0, total, batch_size):
            batch = signatures[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size

            print(f"   Batch {batch_num}/{total_batches}...", end='', flush=True)

            for sig_info in batch:
                sig = sig_info['signature']
                tx_data = self.get_transaction_details(sig)

                if tx_data:
                    parsed = self.parse_transaction(tx_data)
                    if parsed:
                        parsed_txs.append(parsed)

            print(f" ✓ ({len(parsed_txs)} processed)")

        return parsed_txs

    def analyze_wallet(self, address: str) -> Dict[str, Any]:
        """
        Comprehensive wallet analysis.

        Returns:
            Dict with balance, tx history, and basic statistics
        """
        print(f"\n{'='*70}")
        print(f"🔎 ANALYZING WALLET: {address}")
        print(f"{'='*70}\n")

        # Get current balance
        balance = self.get_wallet_balance(address)

        # Get transaction history
        signatures = self.get_transaction_history(address, limit=1000)

        # Process transactions
        parsed_txs = self.batch_process_transactions(signatures[:100])  # Limit for speed

        # Basic statistics
        total_fees = sum(tx.get('fee', 0) for tx in parsed_txs)
        successful_txs = sum(1 for tx in parsed_txs if tx.get('success', False))

        analysis = {
            'address': address,
            'balance': balance,
            'total_transactions': len(signatures),
            'processed_transactions': len(parsed_txs),
            'successful_transactions': successful_txs,
            'total_fees_lamports': total_fees,
            'total_fees_sol': total_fees / 1e9,
            'parsed_transactions': parsed_txs,
            'raw_signatures': signatures
        }

        return analysis
