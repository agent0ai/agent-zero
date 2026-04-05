Download the stock prices for MSFT, AAPL, and TSLA from each second Monday of 2025.

The second Monday of each month in 2025:
- January: 13th
- February: 10th
- March: 10th
- April: 14th
- May: 12th
- June: 9th
- July: 14th
- August: 11th
- September: 8th
- October: 13th
- November: 10th
- December: 8th

Create a CSV file called `stock_prices.csv` in the current working directory with the following structure:

```csv
date,symbol,open,high,low,close,volume
2025-01-13,MSFT,xxx.xx,xxx.xx,xxx.xx,xxx.xx,xxxxxxx
2025-01-13,AAPL,xxx.xx,xxx.xx,xxx.xx,xxx.xx,xxxxxxx
2025-01-13,TSLA,xxx.xx,xxx.xx,xxx.xx,xxx.xx,xxxxxxx
2025-02-10,MSFT,xxx.xx,xxx.xx,xxx.xx,xxx.xx,xxxxxxx
...

Requirements:

 - All prices should have exactly 2 decimal places
 - Volume should be an integer
 - Date format: YYYY-MM-DD
 - Sort by date, then by symbol alphabetically
 - Include header row
 - Use real market data (you can use yfinance, web scraping, or any available API)