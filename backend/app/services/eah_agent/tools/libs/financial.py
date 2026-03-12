from typing import Optional, Dict, Any
from agno.tools import Toolkit
from pydantic import BaseModel, Field
try:
    import yfinance as yf
except ImportError:
    yf = None

class YFinanceTools(Toolkit):
    _name = "yfinance"
    _label = "金融数据 (YFinance)"
    _description = "获取股票价格、公司信息和分析师推荐"
    """
    使用 YFinance 获取股票市场数据。
    """
    def __init__(self):
        super().__init__(name="yfinance_tools")
        self.register(self.get_stock_price)
        self.register(self.get_company_info)
        self.register(self.get_analyst_recommendations)

    def get_stock_price(self, symbol: str) -> str:
        """Get the current stock price for a given symbol."""
        if yf is None:
            return "Error: yfinance package is not installed. Please install it using `pip install yfinance`."
        try:
            ticker = yf.Ticker(symbol)
            # Using history to get the latest close price safely
            history = ticker.history(period="1d")
            if history.empty:
                return f"Could not find price for {symbol}"
            price = history['Close'].iloc[-1]
            return f"Current price for {symbol}: {price:.2f} {ticker.info.get('currency', 'USD')}"
        except Exception as e:
            return f"Error fetching price for {symbol}: {str(e)}"

    def get_company_info(self, symbol: str) -> str:
        """Get company information (Sector, Industry, Market Cap, PE Ratio)."""
        if yf is None:
            return "Error: yfinance package is not installed. Please install it using `pip install yfinance`."
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            keys = ['longName', 'sector', 'industry', 'marketCap', 'trailingPE', 'forwardPE', 'dividendYield', 'website', 'longBusinessSummary']
            summary = {k: info.get(k) for k in keys if k in info}
            return str(summary)
        except Exception as e:
            return f"Error fetching info for {symbol}: {str(e)}"
    
    def get_analyst_recommendations(self, symbol: str) -> str:
        """Get analyst recommendations for a stock."""
        if yf is None:
            return "Error: yfinance package is not installed. Please install it using `pip install yfinance`."
        try:
            ticker = yf.Ticker(symbol)
            recs = ticker.recommendations
            if recs is None or recs.empty:
                return "No recommendations found."
            # Return last 5 recommendations
            return recs.tail(5).to_markdown(index=False)
        except Exception as e:
            return f"Error fetching recommendations: {str(e)}"

    class Config(BaseModel):
        pass

class OpenBBTools(Toolkit):
    _name = "openbb"
    _label = "OpenBB 终端"
    _description = "专业的金融分析平台集成"
    """
    使用 OpenBB 平台进行金融分析。
    注意：需要安装 'openbb' 包。
    """
    api_key: Optional[str] = None

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(name="openbb_tools")
        self.api_key = api_key
        # We only register a health check or basic info for now as OpenBB is large
        self.register(self.get_market_status)

    def get_market_status(self) -> str:
        """Get general market status (Placeholder)."""
        return "OpenBB tools are initialized. (Full integration pending API design)"

    class Config(BaseModel):
        api_key: Optional[str] = Field(None, description="OpenBB Personal Access Token (PAT)")
