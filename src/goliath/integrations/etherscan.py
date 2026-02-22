"""
Etherscan Integration — Ethereum blockchain data via the Etherscan API.

SETUP INSTRUCTIONS
==================

1. Go to https://etherscan.io/ and create a free account.

2. Navigate to https://etherscan.io/myapikey.

3. Click "Add" to create a new API key.

4. Copy the key and add to your .env:
     ETHERSCAN_API_KEY=your-api-key

IMPORTANT NOTES
===============
- API docs: https://docs.etherscan.io/
- Free tier: 5 calls/second, 100,000 calls/day.
- Pro plans available for higher limits and additional endpoints.
- Base URL: https://api.etherscan.io/api
- For testnets, set ETHERSCAN_BASE_URL (e.g. https://api-sepolia.etherscan.io/api).

Usage:
    from goliath.integrations.etherscan import EtherscanClient

    eth = EtherscanClient()

    # Get ETH balance for an address
    balance = eth.get_balance("0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe")

    # Get transaction list
    txns = eth.get_transactions("0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe")

    # Get internal transactions
    internal = eth.get_internal_transactions("0x...")

    # Get ERC-20 token transfers
    tokens = eth.get_token_transfers("0x...", contract_address="0x...")

    # Get current ETH price
    price = eth.get_eth_price()

    # Get gas oracle (gas prices)
    gas = eth.get_gas_oracle()

    # Get contract ABI
    abi = eth.get_contract_abi("0x...")

    # Get block by number
    block = eth.get_block_by_number(12345678)

    # Get ERC-20 token supply
    supply = eth.get_token_supply("0x...")
"""

import requests

from goliath import config

_DEFAULT_BASE = "https://api.etherscan.io/api"


class EtherscanClient:
    """Etherscan API client for Ethereum blockchain data."""

    def __init__(self):
        if not config.ETHERSCAN_API_KEY:
            raise RuntimeError(
                "ETHERSCAN_API_KEY is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/etherscan.py for setup instructions."
            )

        self.api_key = config.ETHERSCAN_API_KEY
        self.base_url = (
            getattr(config, "ETHERSCAN_BASE_URL", "") or _DEFAULT_BASE
        )
        self.session = requests.Session()

    # -- Accounts --------------------------------------------------------------

    def get_balance(self, address: str) -> str:
        """Get ETH balance for an address (in Wei).

        Args:
            address: Ethereum address.

        Returns:
            Balance in Wei as a string.
        """
        return self._get(
            module="account", action="balance",
            address=address, tag="latest",
        )

    def get_multi_balance(self, addresses: list[str]) -> list[dict]:
        """Get ETH balance for multiple addresses.

        Args:
            addresses: List of Ethereum addresses (max 20).

        Returns:
            List of dicts with "account" and "balance".
        """
        return self._get(
            module="account", action="balancemulti",
            address=",".join(addresses), tag="latest",
        )

    def get_transactions(
        self,
        address: str,
        start_block: int = 0,
        end_block: int = 99999999,
        page: int = 1,
        offset: int = 100,
        sort: str = "desc",
    ) -> list[dict]:
        """Get normal transactions for an address.

        Args:
            address:     Ethereum address.
            start_block: Start block number.
            end_block:   End block number.
            page:        Page number.
            offset:      Results per page (max 10000).
            sort:        "asc" or "desc".

        Returns:
            List of transaction dicts.
        """
        return self._get(
            module="account", action="txlist",
            address=address, startblock=start_block, endblock=end_block,
            page=page, offset=offset, sort=sort,
        )

    def get_internal_transactions(
        self,
        address: str,
        start_block: int = 0,
        end_block: int = 99999999,
        page: int = 1,
        offset: int = 100,
    ) -> list[dict]:
        """Get internal transactions for an address.

        Args:
            address:     Ethereum address.
            start_block: Start block number.
            end_block:   End block number.
            page:        Page number.
            offset:      Results per page.

        Returns:
            List of internal transaction dicts.
        """
        return self._get(
            module="account", action="txlistinternal",
            address=address, startblock=start_block, endblock=end_block,
            page=page, offset=offset,
        )

    def get_token_transfers(
        self,
        address: str,
        contract_address: str | None = None,
        page: int = 1,
        offset: int = 100,
    ) -> list[dict]:
        """Get ERC-20 token transfer events.

        Args:
            address:          Ethereum address.
            contract_address: Filter by token contract (optional).
            page:             Page number.
            offset:           Results per page.

        Returns:
            List of transfer event dicts.
        """
        kwargs: dict = {
            "module": "account", "action": "tokentx",
            "address": address, "page": page, "offset": offset,
        }
        if contract_address:
            kwargs["contractaddress"] = contract_address
        return self._get(**kwargs)

    # -- Contracts -------------------------------------------------------------

    def get_contract_abi(self, address: str) -> str:
        """Get the ABI for a verified contract.

        Args:
            address: Contract address.

        Returns:
            ABI JSON string.
        """
        return self._get(module="contract", action="getabi", address=address)

    def get_contract_source(self, address: str) -> list[dict]:
        """Get source code for a verified contract.

        Args:
            address: Contract address.

        Returns:
            List of source code dicts.
        """
        return self._get(
            module="contract", action="getsourcecode", address=address
        )

    # -- Blocks ----------------------------------------------------------------

    def get_block_by_number(self, block_number: int) -> dict:
        """Get block and uncle rewards by block number.

        Args:
            block_number: Block number.

        Returns:
            Block reward dict.
        """
        return self._get(
            module="block", action="getblockreward",
            blockno=block_number,
        )

    def get_block_countdown(self, block_number: int) -> dict:
        """Get estimated time until a block is mined.

        Args:
            block_number: Target block number.

        Returns:
            Dict with countdown info.
        """
        return self._get(
            module="block", action="getblockcountdown",
            blockno=block_number,
        )

    # -- Stats -----------------------------------------------------------------

    def get_eth_price(self) -> dict:
        """Get current ETH price in USD and BTC.

        Returns:
            Dict with "ethbtc", "ethbtc_timestamp", "ethusd", "ethusd_timestamp".
        """
        return self._get(module="stats", action="ethprice")

    def get_eth_supply(self) -> str:
        """Get total ETH supply.

        Returns:
            Total supply in Wei as a string.
        """
        return self._get(module="stats", action="ethsupply")

    def get_token_supply(self, contract_address: str) -> str:
        """Get ERC-20 token total supply.

        Args:
            contract_address: Token contract address.

        Returns:
            Total supply as a string.
        """
        return self._get(
            module="stats", action="tokensupply",
            contractaddress=contract_address,
        )

    # -- Gas -------------------------------------------------------------------

    def get_gas_oracle(self) -> dict:
        """Get current gas prices (safe, propose, fast).

        Returns:
            Dict with "SafeGasPrice", "ProposeGasPrice", "FastGasPrice".
        """
        return self._get(module="gastracker", action="gasoracle")

    def get_gas_estimate(self, gas_price: int) -> str:
        """Get estimated confirmation time for a gas price.

        Args:
            gas_price: Gas price in Gwei.

        Returns:
            Estimated seconds as a string.
        """
        return self._get(
            module="gastracker", action="gasestimate",
            gasprice=gas_price,
        )

    # -- internal helpers ------------------------------------------------------

    def _get(self, **params) -> dict | list | str:
        params["apikey"] = self.api_key
        resp = self.session.get(self.base_url, params=params)
        resp.raise_for_status()
        body = resp.json()
        if body.get("status") == "0" and body.get("message") != "No transactions found":
            raise RuntimeError(
                f"Etherscan API error: {body.get('message', '')} — "
                f"{body.get('result', '')}"
            )
        return body.get("result", body)
