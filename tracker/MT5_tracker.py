from v20 import Context

API_KEY = "YOUR_OANDA_API_KEY"
ACCOUNT_ID = "YOUR_ACCOUNT_ID"
HOST = "api-fxpractice.oanda.com"  # demo; live = api-fxtrade.oanda.com

ctx = Context(HOST, 443, token=API_KEY)

def get_account_data():
    """Fetch current account info and simple P&L"""
    # Get balance & equity
    resp = ctx.account.summary(ACCOUNT_ID)
    acct = resp.get("account", {})
    balance = float(acct.get("balance", 0))
    equity = float(acct.get("NAV", 0))
    
    # Total profit % relative to balance
    total_profit_pct = (equity - balance) / balance * 100
    
    # Simple alerts
    alerts = {
        "profit_target": total_profit_pct >= 3,
        "overall_drawdown": (balance - equity) / balance * 100 > 2.5
    }
    
    return {
        "balance": balance,
        "equity": equity,
        "total_profit_pct": total_profit_pct,
        "alerts": alerts
    }
