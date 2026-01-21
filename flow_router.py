"""
Advanced Flow Routing Engine
Multi-hop transaction tracing and route mapping
"""

from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict
import networkx as nx
from utils import format_sol_amount, truncate_address, format_timestamp

# Known program labels for better routing descriptions
PROGRAM_LABELS = {
    'JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4': 'Jupiter Aggregator',
    'JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB': 'Jupiter V4',
    '675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8': 'Raydium AMM',
    'RVKd61ztZW9GUwhRbbLoYVRE5Xf1B2tVscKqwZqXgEr': 'Raydium V4',
    '9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin': 'Serum DEX',
    'srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX': 'Serum DEX V3',
    'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA': 'SPL Token Program',
    '11111111111111111111111111111111': 'System Program',
    'So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo': 'Solend',
    'PhoeNiXZ8ByJGLkxNfZRnkUfjvmuYqLR89jjFHGqdXY': 'Phoenix',
    'whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc': 'Orca Whirlpools'
}

class FlowRouter:
    """
    Advanced transaction flow routing and tracing.
    Builds directed graphs of SOL/token movements across wallets and programs.
    """

    def __init__(self):
        self.flow_graph = nx.DiGraph()
        self.routes = []
        self.flow_stats = defaultdict(lambda: {'in': 0, 'out': 0, 'net': 0})

    def get_program_label(self, program_id: str) -> str:
        """Get human-readable label for program ID."""
        return PROGRAM_LABELS.get(program_id, truncate_address(program_id))

    def extract_transfers(self, tx_data: Dict) -> List[Dict]:
        """
        Extract SOL/token transfers from parsed transaction.

        Returns:
            List of transfer dicts with source, destination, amount
        """
        transfers = []

        if not tx_data or not tx_data.get('success', False):
            return transfers

        accounts = tx_data.get('accounts', [])
        pre_balances = tx_data.get('pre_balances', [])
        post_balances = tx_data.get('post_balances', [])

        # Calculate balance changes for each account
        for i, account in enumerate(accounts):
            if i < len(pre_balances) and i < len(post_balances):
                pre = pre_balances[i]
                post = post_balances[i]
                delta = post - pre

                if delta != 0:
                    transfers.append({
                        'account': account,
                        'delta_lamports': delta,
                        'delta_sol': delta / 1e9,
                        'pre_balance': pre,
                        'post_balance': post
                    })

        return transfers

    def build_route_chain(self, tx_data: Dict) -> List[Dict]:
        """
        Build a chain of operations for a single transaction.
        Represents the flow: Source → Program → Destination

        Returns:
            List of route steps with descriptions
        """
        route_chain = []

        if not tx_data or not tx_data.get('success', False):
            return route_chain

        signature = tx_data.get('signature', 'Unknown')
        timestamp = tx_data.get('timestamp', 0)
        programs = tx_data.get('programs', [])
        transfers = self.extract_transfers(tx_data)

        # Build route steps from transfers and programs
        for transfer in transfers:
            account = transfer['account']
            delta = transfer['delta_sol']

            # Determine direction
            if delta > 0:
                direction = 'INFLOW'
                description = f"+{abs(delta):.4f} SOL"
            else:
                direction = 'OUTFLOW'
                description = f"-{abs(delta):.4f} SOL"

            # Add programs involved
            program_labels = [self.get_program_label(p) for p in programs[:3]]
            program_str = ' → '.join(program_labels) if program_labels else 'Direct Transfer'

            route_chain.append({
                'signature': signature,
                'timestamp': timestamp,
                'account': account,
                'direction': direction,
                'amount_sol': abs(delta),
                'amount_lamports': abs(transfer['delta_lamports']),
                'programs': program_str,
                'description': description,
                'pre_balance': transfer['pre_balance'],
                'post_balance': transfer['post_balance']
            })

        return route_chain

    def trace_flows(self, transactions: List[Dict]) -> Dict[str, Any]:
        """
        Trace all flows across multiple transactions.
        Builds a complete flow graph and calculates statistics.

        Args:
            transactions: List of parsed transaction dicts

        Returns:
            Dict with flow graph, routes, and statistics
        """
        print(f"\n🌊 Tracing transaction flows...")

        all_routes = []
        account_flows = defaultdict(lambda: {'inflows': 0, 'outflows': 0})

        for i, tx in enumerate(transactions):
            if (i + 1) % 20 == 0:
                print(f"   Processed {i + 1}/{len(transactions)} transactions...")

            route_chain = self.build_route_chain(tx)

            for step in route_chain:
                all_routes.append(step)

                # Update flow statistics
                account = step['account']
                amount = step['amount_sol']

                if step['direction'] == 'INFLOW':
                    account_flows[account]['inflows'] += amount
                else:
                    account_flows[account]['outflows'] += amount

                # Add to graph
                if step['programs'] != 'Direct Transfer':
                    self.flow_graph.add_edge(
                        account,
                        step['programs'],
                        weight=amount,
                        signature=step['signature']
                    )

        # Calculate net flows
        for account, flows in account_flows.items():
            flows['net'] = flows['inflows'] - flows['outflows']

        print(f"✅ Traced {len(all_routes)} flow events")

        return {
            'routes': all_routes,
            'account_flows': dict(account_flows),
            'graph': self.flow_graph,
            'total_flow_events': len(all_routes)
        }

    def identify_multi_hop_chains(
        self,
        transactions: List[Dict],
        min_hops: int = 2
    ) -> List[Dict]:
        """
        Identify complex multi-hop transaction chains.
        Example: Exchange → Jupiter → Raydium → Token Mint

        Args:
            transactions: List of parsed transactions
            min_hops: Minimum number of hops to qualify

        Returns:
            List of multi-hop chain descriptions
        """
        chains = []

        for tx in transactions:
            programs = tx.get('programs', [])
            if len(programs) >= min_hops:
                chain_labels = [self.get_program_label(p) for p in programs]

                chains.append({
                    'signature': tx.get('signature', 'Unknown'),
                    'timestamp': tx.get('timestamp', 0),
                    'hop_count': len(programs),
                    'chain': ' → '.join(chain_labels),
                    'programs': programs
                })

        return sorted(chains, key=lambda x: x['hop_count'], reverse=True)

    def find_counterparties(
        self,
        transactions: List[Dict],
        target_address: str
    ) -> Dict[str, int]:
        """
        Find all counterparty addresses that interacted with target.

        Returns:
            Dict mapping counterparty address to interaction count
        """
        counterparties = defaultdict(int)

        for tx in transactions:
            accounts = tx.get('accounts', [])

            if target_address in accounts:
                for account in accounts:
                    if account != target_address and account not in PROGRAM_LABELS:
                        counterparties[account] += 1

        return dict(counterparties)

    def generate_flow_summary(self, flow_data: Dict) -> str:
        """
        Generate human-readable flow summary.

        Returns:
            Formatted text summary of flows
        """
        routes = flow_data['routes']
        account_flows = flow_data['account_flows']

        if not routes:
            return "No significant flows detected."

        # Find top movers
        top_inflows = sorted(
            account_flows.items(),
            key=lambda x: x[1]['inflows'],
            reverse=True
        )[:5]

        top_outflows = sorted(
            account_flows.items(),
            key=lambda x: x[1]['outflows'],
            reverse=True
        )[:5]

        summary = []
        summary.append(f"\n📊 FLOW SUMMARY")
        summary.append(f"{'='*70}")
        summary.append(f"Total Flow Events: {len(routes)}")
        summary.append(f"Unique Accounts: {len(account_flows)}")

        summary.append(f"\n🔽 Top Inflows:")
        for account, flows in top_inflows:
            addr_display = truncate_address(account)
            summary.append(
                f"   {addr_display}: +{flows['inflows']:.4f} SOL "
                f"(Net: {flows['net']:+.4f} SOL)"
            )

        summary.append(f"\n🔼 Top Outflows:")
        for account, flows in top_outflows:
            addr_display = truncate_address(account)
            summary.append(
                f"   {addr_display}: -{flows['outflows']:.4f} SOL "
                f"(Net: {flows['net']:+.4f} SOL)"
            )

        return '\n'.join(summary)

    def create_flow_table(self, routes: List[Dict], limit: int = 20) -> List[List[Any]]:
        """
        Create table data for flow routes display.

        Returns:
            List of rows for tabulate
        """
        rows = []

        for route in routes[:limit]:
            rows.append([
                route['signature'][:8] + '...',
                format_timestamp(route['timestamp']),
                truncate_address(route['account']),
                route['direction'],
                f"{route['amount_sol']:.4f} SOL",
                route['programs'][:40]
            ])

        return rows

    def analyze_route_patterns(self, routes: List[Dict]) -> Dict[str, Any]:
        """
        Analyze patterns in route data.
        Detects common programs, clustering, timing patterns.

        Returns:
            Dict with pattern statistics
        """
        if not routes:
            return {}

        # Program frequency
        program_counts = defaultdict(int)
        for route in routes:
            programs = route.get('programs', '')
            if programs and programs != 'Direct Transfer':
                program_counts[programs] += 1

        # Timing analysis
        timestamps = [r['timestamp'] for r in routes if r.get('timestamp')]
        time_deltas = []
        if len(timestamps) > 1:
            sorted_times = sorted(timestamps)
            time_deltas = [sorted_times[i] - sorted_times[i-1] for i in range(1, len(sorted_times))]

        avg_time_delta = sum(time_deltas) / len(time_deltas) if time_deltas else 0

        # Direction analysis
        inflows = sum(1 for r in routes if r['direction'] == 'INFLOW')
        outflows = sum(1 for r in routes if r['direction'] == 'OUTFLOW')

        return {
            'top_programs': sorted(
                program_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            'avg_time_between_txs': avg_time_delta,
            'inflow_count': inflows,
            'outflow_count': outflows,
            'flow_balance': inflows - outflows
        }
