import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Stock Metrics Dashboard",
    page_icon="📈",
    layout="wide"
)

# Title
st.title("📊 Stock Metrics Dashboard")
st.markdown("View key financial metrics for any publicly traded company")

# Sidebar for input
st.sidebar.header("Stock Selection")
ticker = st.sidebar.text_input("Enter Stock Ticker", value="AAPL").upper()
period = st.sidebar.selectbox(
    "Data Period",
    options=["1y", "2y", "3y", "5y"],
    index=2
)

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_stock_data(ticker_symbol, period):
    """Fetch stock data and metrics from Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # Get historical data for growth calculations
        hist = stock.history(period=period)
        
        # Get financial statements
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cashflow = stock.cashflow
        
        # Get info
        info = stock.info
        
        # Calculate metrics
        metrics = {}
        
        # 1. Revenue Growth (YoY)
        if not financials.empty and 'Total Revenue' in financials.index:
            revenues = financials.loc['Total Revenue']
            if len(revenues) >= 2:
                latest_rev = revenues.iloc[0]
                prev_rev = revenues.iloc[1]
                metrics['Revenue Growth (YoY)'] = ((latest_rev - prev_rev) / prev_rev) * 100
            else:
                metrics['Revenue Growth (YoY)'] = None
        else:
            metrics['Revenue Growth (YoY)'] = None
        
        # 2. Gross Profit Margin
        if not financials.empty and 'Gross Profit' in financials.index and 'Total Revenue' in financials.index:
            gross_profit = financials.loc['Gross Profit'].iloc[0]
            revenue = financials.loc['Total Revenue'].iloc[0]
            metrics['Gross Profit Margin'] = (gross_profit / revenue) * 100 if revenue != 0 else None
        else:
            metrics['Gross Profit Margin'] = None
        
        # 3. Operating Margin
        if not financials.empty and 'Operating Income' in financials.index and 'Total Revenue' in financials.index:
            operating_income = financials.loc['Operating Income'].iloc[0]
            revenue = financials.loc['Total Revenue'].iloc[0]
            metrics['Operating Margin'] = (operating_income / revenue) * 100 if revenue != 0 else None
        else:
            metrics['Operating Margin'] = None
        
        # 4. Free Cash Flow (FCF)
        if not cashflow.empty and 'Free Cash Flow' in cashflow.index:
            fcf = cashflow.loc['Free Cash Flow'].iloc[0]
            metrics['Free Cash Flow (FCF)'] = fcf
        else:
            metrics['Free Cash Flow (FCF)'] = None
        
        # 5. Free Cash Flow Yield
        if metrics['Free Cash Flow (FCF)'] is not None and 'marketCap' in info:
            market_cap = info.get('marketCap')
            if market_cap:
                metrics['Free Cash Flow Yield'] = (metrics['Free Cash Flow (FCF)'] / market_cap) * 100
            else:
                metrics['Free Cash Flow Yield'] = None
        else:
            metrics['Free Cash Flow Yield'] = None
        
        # 6. Net Debt / EBITDA
        net_debt = None
        ebitda = None
        
        if 'Total Debt' in balance_sheet.index and 'Cash And Cash Equivalents' in balance_sheet.index:
            total_debt = balance_sheet.loc['Total Debt'].iloc[0] if 'Total Debt' in balance_sheet.index else 0
            cash = balance_sheet.loc['Cash And Cash Equivalents'].iloc[0] if 'Cash And Cash Equivalents' in balance_sheet.index else 0
            net_debt = total_debt - cash
        
        if 'EBITDA' in financials.index:
            ebitda = financials.loc['EBITDA'].iloc[0]
        
        if net_debt is not None and ebitda is not None and ebitda != 0:
            metrics['Net Debt / EBITDA'] = net_debt / ebitda
        else:
            metrics['Net Debt / EBITDA'] = None
        
        # 7. EPS Growth (YoY)
        if not financials.empty and 'Net Income' in financials.index:
            net_incomes = financials.loc['Net Income']
            if len(net_incomes) >= 2:
                shares_outstanding = info.get('sharesOutstanding', 1)
                eps_latest = net_incomes.iloc[0] / shares_outstanding
                eps_prev = net_incomes.iloc[1] / shares_outstanding
                metrics['Earnings Per Share (EPS) Growth'] = ((eps_latest - eps_prev) / abs(eps_prev)) * 100
            else:
                metrics['Earnings Per Share (EPS) Growth'] = None
        else:
            metrics['Earnings Per Share (EPS) Growth'] = None
        
        # 8. PEG Ratio
        pe_ratio = info.get('trailingPE')
        eps_growth = metrics.get('Earnings Per Share (EPS) Growth')
        
        if pe_ratio is not None and eps_growth is not None and eps_growth != 0:
            metrics['PEG Ratio'] = pe_ratio / eps_growth
        else:
            metrics['PEG Ratio'] = None
        
        # Additional info for display
        company_info = {
            'Name': info.get('longName', ticker_symbol),
            'Sector': info.get('sector', 'N/A'),
            'Industry': info.get('industry', 'N/A'),
            'Market Cap': info.get('marketCap', 'N/A'),
            'Current Price': hist['Close'].iloc[-1] if not hist.empty else None,
            '52W High': info.get('fiftyTwoWeekHigh', 'N/A'),
            '52W Low': info.get('fiftyTwoWeekLow', 'N/A'),
        }
        
        return metrics, company_info, hist
        
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None, None, None

# Main content
if ticker:
    with st.spinner(f"Fetching data for {ticker}..."):
        metrics, company_info, hist = get_stock_data(ticker, period)
    
    if metrics and company_info:
        # Company info section
        st.header(f"🏢 {company_info['Name']} ({ticker})")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Sector", company_info['Sector'])
        with col2:
            st.metric("Industry", company_info['Industry'])
        with col3:
            market_cap_str = f"${company_info['Market Cap']:,.0f}" if isinstance(company_info['Market Cap'], (int, float)) else company_info['Market Cap']
            st.metric("Market Cap", market_cap_str)
        with col4:
            if company_info['Current Price']:
                st.metric("Current Price", f"${company_info['Current Price']:.2f}")
        
        # Metrics display
        st.header("📈 Key Financial Metrics")
        
        # Create two columns for metrics
        col1, col2 = st.columns(2)
        
        # Define metric categories for display
        metric_categories = {
            "Growth & Demand": ["Revenue Growth (YoY)", "Earnings Per Share (EPS) Growth"],
            "Competitive Advantage (Moat)": ["Gross Profit Margin"],
            "Management Efficiency": ["Operating Margin"],
            "Financial Health & Value": ["Free Cash Flow (FCF)", "Free Cash Flow Yield"],
            "Risk & Leverage": ["Net Debt / EBITDA"],
            "Valuation vs. Growth": ["PEG Ratio"]
        }
        
        # Display metrics with formatting
        for category, metric_names in metric_categories.items():
            with st.expander(f"**{category}**"):
                for metric_name in metric_names:
                    value = metrics.get(metric_name)
                    if value is not None:
                        if metric_name in ["Revenue Growth (YoY)", "Earnings Per Share (EPS) Growth"]:
                            formatted_value = f"{value:.2f}%"
                            delta_color = "normal"
                        elif metric_name in ["Gross Profit Margin", "Operating Margin", "Free Cash Flow Yield"]:
                            formatted_value = f"{value:.2f}%"
                        elif metric_name == "Free Cash Flow (FCF)":
                            formatted_value = f"${value:,.0f}"
                        elif metric_name == "Net Debt / EBITDA":
                            formatted_value = f"{value:.2f}x"
                        elif metric_name == "PEG Ratio":
                            formatted_value = f"{value:.2f}"
                        else:
                            formatted_value = f"{value:,.2f}"
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            st.markdown(f"**{metric_name}**")
                        with col2:
                            st.markdown(formatted_value)
                    else:
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            st.markdown(f"**{metric_name}**")
                        with col2:
                            st.markdown("*Data not available*")
        
        # Price chart
        st.header("📉 Price History")
        if not hist.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist['Close'],
                mode='lines',
                name='Close Price',
                line=dict(color='#0066cc', width=2)
            ))
            
            fig.update_layout(
                title=f"{ticker} - Stock Price",
                xaxis_title="Date",
                yaxis_title="Price ($)",
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Metrics explanation
        st.header("📚 Metrics Explanation")
        with st.expander("Click to learn about each metric"):
            st.markdown("""
            - **Revenue Growth (YoY)**: Year-over-year revenue increase, indicating demand for products/services
            - **Gross Profit Margin**: (Revenue - COGS)/Revenue - shows pricing power and cost efficiency
            - **Operating Margin**: Operating Income/Revenue - measures management efficiency
            - **Free Cash Flow (FCF)**: Cash from operations minus capital expenditures
            - **Free Cash Flow Yield**: FCF/Market Cap - cash return relative to price
            - **Net Debt / EBITDA**: Leverage ratio - lower is better (<3x is healthy)
            - **EPS Growth (YoY)**: Year-over-year earnings per share growth
            - **PEG Ratio**: P/E divided by EPS growth rate - <1 suggests undervaluation
            """)
    else:
        st.error(f"Could not fetch data for ticker '{ticker}'. Please check the ticker symbol and try again.")
else:
    st.info("👈 Enter a stock ticker in the sidebar to get started (e.g., AAPL, MSFT, GOOGL)")

# Footer
st.markdown("---")
st.caption("Data provided by Yahoo Finance. For informational purposes only.")
