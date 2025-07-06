# Enhanced Stock Analysis System

## Introduction

The Enhanced Stock Analysis System is a web-based application that provides advanced stock analysis capabilities. It supports real-time streaming of analysis results using Server-Sent Events (SSE) and integrates AI models for deep analysis. The system is designed to help users make informed investment decisions by analyzing various aspects of stocks, including technical indicators, fundamental data, and market sentiment.

## Configuration

The system uses a configuration file (`config.json`) to manage various settings, including API keys, analysis weights, streaming settings, and analysis parameters. Below is an example configuration file:

```json
{
  "api_keys": {
    "openai": "",
    "anthropic": "",
    "zhipu": "",
    "notes": "Please fill in your API keys"
  },
  "ai": {
    "model_preference": "openai",
    "models": {
      "openai": "gpt-4o-mini",
      "anthropic": "claude-3-haiku-20240307",
      "zhipu": "chatglm_turbo"
    },
    "max_tokens": 4000,
    "temperature": 0.7,
    "api_base_urls": {
      "openai": "https://api.openai.com/v1",
      "notes": "Modify the above URL if using a proxy API"
    }
  },
  "analysis_weights": {
    "technical": 0.4,
    "fundamental": 0.4,
    "sentiment": 0.2,
    "notes": "The sum of weights should be 1.0"
  },
  "cache": {
    "price_hours": 1,
    "fundamental_hours": 6,
    "news_hours": 2
  },
  "streaming": {
    "enabled": true,
    "show_thinking": false,
    "delay": 0.05
  },
  "analysis_params": {
    "max_news_count": 100,
    "technical_period_days": 180,
    "financial_indicators_count": 25
  },
  "web_auth": {
    "enabled": false,
    "password": "",
    "session_timeout": 3600,
    "notes": "Web interface password authentication settings"
  },
  "_metadata": {
    "version": "3.0.0-web-streaming",
    "created": "2025-07-06T22:37:08+08:00",
    "description": "Web-based AI stock analysis system configuration file (supports AI streaming output)"
  }
}
```

## Stock Analysis Strategies

The core stock analysis strategies and methods are implemented in the `web_stock_analyzer.py` file. Below are the key components:

### Initialization and Configuration

The `WebStockAnalyzer` class initializes the analyzer with configuration settings, including API keys, analysis weights, streaming settings, and analysis parameters.

### Data Caching

The system implements caching mechanisms for price data, fundamental data, and news data to improve performance and reduce redundant API calls.

### Stock Data Retrieval

The `get_stock_data` method fetches historical stock price data and handles column mappings to ensure compatibility with the analysis methods.

### Fundamental Analysis

The `get_comprehensive_fundamental_data` method retrieves and calculates 25 core financial indicators, valuation metrics, performance forecasts, dividend information, and industry analysis.

### News Analysis

The `get_comprehensive_news_data` method collects and processes company news, announcements, research reports, and industry news. The `calculate_advanced_sentiment_analysis` method performs advanced sentiment analysis on news data using custom sentiment dictionaries.

### Technical Analysis

The `calculate_technical_indicators` method calculates technical indicators such as moving averages, RSI, MACD, Bollinger Bands, and volume analysis. Below are the details of each indicator:

#### Moving Averages (MA)
- **Parameters**: 
  - `window`: The number of periods to calculate the moving average.
- **Usage**: 
  - The method calculates moving averages for different periods (e.g., 5, 10, 20, 60 days) to identify trends. 
  - If the current price is above the moving averages, it indicates an uptrend, and vice versa.

#### Relative Strength Index (RSI)
- **Parameters**: 
  - `window`: The number of periods to calculate the RSI (default is 14).
- **Usage**: 
  - The RSI is used to identify overbought or oversold conditions. 
  - An RSI above 70 indicates overbought conditions, while an RSI below 30 indicates oversold conditions.

#### Moving Average Convergence Divergence (MACD)
- **Parameters**: 
  - `span1`: The number of periods for the fast EMA (default is 12).
  - `span2`: The number of periods for the slow EMA (default is 26).
  - `signal_span`: The number of periods for the signal line (default is 9).
- **Usage**: 
  - The MACD is used to identify changes in the strength, direction, momentum, and duration of a trend. 
  - A bullish signal is generated when the MACD line crosses above the signal line, and a bearish signal is generated when the MACD line crosses below the signal line.

#### Bollinger Bands (BB)
- **Parameters**: 
  - `window`: The number of periods to calculate the moving average (default is 20).
  - `std_dev`: The number of standard deviations to calculate the upper and lower bands (default is 2).
- **Usage**: 
  - Bollinger Bands are used to measure market volatility. 
  - The bands contract during low volatility and expand during high volatility. 
  - Prices tend to bounce within the bands, and a move outside the bands can indicate a continuation of the trend.

#### Volume Analysis
- **Usage**: 
  - Volume analysis is used to confirm price trends. 
  - Increasing volume during an uptrend indicates strong buying interest, while increasing volume during a downtrend indicates strong selling interest.


### Scoring

The system calculates scores for technical, fundamental, and sentiment analysis using the `calculate_technical_score`, `calculate_fundamental_score`, and `calculate_sentiment_score` methods. These scores are combined into a comprehensive score using the `calculate_comprehensive_score` method.

### Investment Recommendations

The `generate_recommendation` method generates investment recommendations based on the comprehensive score.

### AI Enhanced Analysis

The `generate_ai_analysis` method uses AI models to generate detailed stock analysis reports. It supports streaming output for real-time updates.

## Web Integration

The stock analysis strategies are integrated into a web application using the `flask_web_server.py` file. The web server provides endpoints for initiating stock analysis and streaming results using SSE.

### Server-Sent Events (SSE)

The `SSEManager` class manages SSE connections and broadcasts messages to clients. The `StreamingAnalyzer` class handles the streaming of analysis results and progress updates to clients.

### Flask Endpoints

The web server provides the following endpoints:

- `/api/analyze_stream`: Initiates a single stock analysis with streaming output.
- `/api/batch_analyze_stream`: Initiates batch stock analysis with streaming output.
- `/api/status`: Checks the system status.
- `/api/task_status/<stock_code>`: Retrieves the status of an ongoing analysis task.
- `/api/system_info`: Retrieves system information.

## Usage

To use the web application for stock analysis, follow these steps:

1. **Start the Web Server**: Run the `flask_web_server.py` file to start the web server.
2. **Access the Web Interface**: Open a web browser and navigate to `http://localhost:5000`.
3. **Initiate Stock Analysis**: Enter the stock code in the input field and click the "Start Analysis" button to initiate the analysis. The results will be streamed in real-time using SSE.
4. **View Results**: The analysis results, including scores and investment recommendations, will be displayed on the web interface.

## Conclusion

The Enhanced Stock Analysis System provides a comprehensive and real-time solution for stock analysis. By leveraging advanced AI models and real-time streaming capabilities, the system helps users make informed investment decisions based on detailed analysis of technical indicators, fundamental data, and market sentiment.
