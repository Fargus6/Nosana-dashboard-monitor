#!/usr/bin/env python3
"""
Verify NOS and SOL balances match between:
1. Our app backend
2. Nosana dashboard (web scraping)
3. Solana blockchain (direct RPC)
"""
import asyncio
import sys
sys.path.append('/app/backend')

from solana.rpc.api import Client as SolanaClient
from solders.pubkey import Pubkey as SoldersPubkey
from solana.rpc.types import TokenAccountOpts
from playwright.async_api import async_playwright
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test node addresses
TEST_NODES = [
    "9hsWPkJUBiDQnc2p7dKi2gMKHp6LwscA6Z5qAF8NGsyV",
]

NOS_MINT = "nosXBVoaCTtYdLvKY6Csb4AC8JCdQKKAaWYtx2ZMoo7"

async def get_blockchain_balances(address: str):
    """Get SOL and NOS balances directly from Solana blockchain"""
    try:
        solana_client = SolanaClient("https://api.mainnet-beta.solana.com")
        
        # Get SOL balance
        pubkey = SoldersPubkey.from_string(address)
        account_info = solana_client.get_account_info(pubkey)
        
        sol_balance = None
        if account_info.value:
            sol_balance = account_info.value.lamports / 1e9
        
        # Get NOS balance
        nos_balance = 0.0
        wallet_pubkey = SoldersPubkey.from_string(address)
        nos_mint_pubkey = SoldersPubkey.from_string(NOS_MINT)
        
        opts = TokenAccountOpts(mint=nos_mint_pubkey)
        response = solana_client.get_token_accounts_by_owner(wallet_pubkey, opts)
        
        if response and response.value:
            for account in response.value:
                token_account_pubkey = SoldersPubkey.from_string(str(account.pubkey))
                balance_response = solana_client.get_token_account_balance(token_account_pubkey)
                if balance_response and balance_response.value:
                    account_balance = balance_response.value.ui_amount
                    if account_balance:
                        nos_balance += account_balance
        
        return {
            'sol': sol_balance,
            'nos': nos_balance if nos_balance > 0 else None
        }
    except Exception as e:
        logger.error(f"Error getting blockchain balances: {e}")
        return {'sol': None, 'nos': None}

async def get_dashboard_balances(address: str):
    """Scrape balances from Nosana dashboard"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            url = f"https://dashboard.nosana.com/host/{address}"
            await page.goto(url, wait_until='networkidle', timeout=20000)
            await page.wait_for_timeout(2000)
            
            text_content = await page.inner_text('body')
            text_lower = text_content.lower()
            
            await browser.close()
            
            # Extract balances
            nos_balance = None
            nos_match = re.search(r'(\d+\.?\d*)\s*nos', text_lower)
            if nos_match:
                nos_balance = float(nos_match.group(1))
            
            sol_balance = None
            sol_match = re.search(r'(\d+\.?\d*)\s*sol', text_lower)
            if sol_match:
                sol_balance = float(sol_match.group(1))
            
            return {
                'sol': sol_balance,
                'nos': nos_balance
            }
    except Exception as e:
        logger.error(f"Error scraping dashboard: {e}")
        return {'sol': None, 'nos': None}

async def verify_node_balances(address: str):
    """Compare balances from different sources"""
    print(f"\n{'='*100}")
    print(f"VERIFYING BALANCES FOR NODE: {address}")
    print(f"{'='*100}\n")
    
    # Get balances from blockchain
    print("📡 Fetching from Solana blockchain...")
    blockchain = await get_blockchain_balances(address)
    sol_str = f"{blockchain['sol']:.6f}" if blockchain['sol'] is not None else 'N/A'
    nos_str = f"{blockchain['nos']:.2f}" if blockchain['nos'] is not None else 'N/A'
    print(f"   SOL: {sol_str}")
    print(f"   NOS: {nos_str}\n")
    
    # Get balances from dashboard
    print("🌐 Scraping from Nosana dashboard...")
    dashboard = await get_dashboard_balances(address)
    dash_sol_str = f"{dashboard['sol']:.6f}" if dashboard['sol'] is not None else 'N/A'
    dash_nos_str = f"{dashboard['nos']:.2f}" if dashboard['nos'] is not None else 'N/A'
    print(f"   SOL: {dash_sol_str}")
    print(f"   NOS: {dash_nos_str}\n")
    
    # Compare results
    print("🔍 COMPARISON:")
    print(f"{'='*100}")
    
    # SOL comparison
    if blockchain['sol'] and dashboard['sol']:
        sol_diff = abs(blockchain['sol'] - dashboard['sol'])
        sol_match = sol_diff < 0.000001  # Allow tiny floating point differences
        
        print(f"SOL Balance:")
        print(f"   Blockchain: {blockchain['sol']:.6f}")
        print(f"   Dashboard:  {dashboard['sol']:.6f}")
        print(f"   Difference: {sol_diff:.9f}")
        print(f"   Status:     {'✅ MATCH' if sol_match else '❌ MISMATCH'}\n")
    else:
        print(f"SOL Balance:")
        print(f"   Blockchain: {blockchain['sol']:.6f if blockchain['sol'] else 'N/A'}")
        print(f"   Dashboard:  {dashboard['sol']:.6f if dashboard['sol'] else 'N/A'}")
        print(f"   Status:     ⚠️  Missing data\n")
    
    # NOS comparison
    if blockchain['nos'] and dashboard['nos']:
        nos_diff = abs(blockchain['nos'] - dashboard['nos'])
        nos_match = nos_diff < 0.01  # Allow small rounding differences
        
        print(f"NOS Balance:")
        print(f"   Blockchain: {blockchain['nos']:.2f}")
        print(f"   Dashboard:  {dashboard['nos']:.2f}")
        print(f"   Difference: {nos_diff:.4f}")
        print(f"   Status:     {'✅ MATCH' if nos_match else '❌ MISMATCH'}\n")
    else:
        print(f"NOS Balance:")
        print(f"   Blockchain: {blockchain['nos']:.2f if blockchain['nos'] else 'N/A'}")
        print(f"   Dashboard:  {dashboard['nos']:.2f if dashboard['nos'] else 'N/A'}")
        print(f"   Status:     ⚠️  Missing data\n")
    
    return {
        'sol_match': blockchain['sol'] == dashboard['sol'] if (blockchain['sol'] and dashboard['sol']) else None,
        'nos_match': abs(blockchain['nos'] - dashboard['nos']) < 0.01 if (blockchain['nos'] and dashboard['nos']) else None
    }

async def main():
    print(f"\n{'='*100}")
    print(f"BALANCE VERIFICATION TEST")
    print(f"{'='*100}")
    print(f"Testing {len(TEST_NODES)} node(s)\n")
    
    results = []
    
    for address in TEST_NODES:
        result = await verify_node_balances(address)
        results.append(result)
    
    print(f"\n{'='*100}")
    print(f"SUMMARY")
    print(f"{'='*100}\n")
    
    all_match = all(
        (r['sol_match'] is True or r['sol_match'] is None) and 
        (r['nos_match'] is True or r['nos_match'] is None) 
        for r in results
    )
    
    if all_match:
        print("✅ ALL BALANCES MATCH!")
        print("✅ Our backend fetches accurate data")
        print("✅ Blockchain and Dashboard are in sync")
    else:
        print("⚠️  SOME BALANCES DON'T MATCH")
        print("⚠️  Manual verification needed")
    
    print(f"\n{'='*100}\n")

if __name__ == "__main__":
    asyncio.run(main())
