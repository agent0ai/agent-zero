import os
import csv
from datetime import datetime


# Expected dates (second Monday of each month in 2025)
EXPECTED_DATES = [
    "2025-01-13", "2025-02-10", "2025-03-10", "2025-04-14",
    "2025-05-12", "2025-06-09", "2025-07-14", "2025-08-11",
    "2025-09-08", "2025-10-13", "2025-11-10", "2025-12-08"
]

EXPECTED_SYMBOLS = ["AAPL", "MSFT", "TSLA"]
EXPECTED_COLUMNS = ["date", "symbol", "open", "high", "low", "close", "volume"]


def execute(runtime_path: str, agent, state: dict) -> dict:
    """Evaluate the stock prices task."""
    result_file = os.path.join(runtime_path, "stock_prices.csv")
    
    scorecard = {
        "score": 0,
        "file_exists": False,
        "header_correct": False,
        "date_count": 0,
        "symbol_count": 0,
        "row_count": 0,
        "format_errors": [],
        "missing_dates": [],
        "missing_symbols": [],
        "data_validation": {}
    }
    
    if not os.path.exists(result_file):
        scorecard["error"] = "stock_prices.csv not found"
        return scorecard
    
    scorecard["file_exists"] = True
    points = 10  # File exists
    
    try:
        with open(result_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            
            # Check header
            if reader.fieldnames:
                header_lower = [h.lower().strip() for h in reader.fieldnames]
                if header_lower == EXPECTED_COLUMNS:
                    scorecard["header_correct"] = True
                    points += 10
                else:
                    scorecard["format_errors"].append(f"Header mismatch: got {reader.fieldnames}")
            
            rows = list(reader)
            scorecard["row_count"] = len(rows)
            
            # Expected: 12 dates × 3 symbols = 36 rows
            expected_rows = len(EXPECTED_DATES) * len(EXPECTED_SYMBOLS)
            
            found_dates = set()
            found_symbols = set()
            valid_rows = 0
            
            for i, row in enumerate(rows):
                row_errors = []
                
                # Normalize keys to lowercase
                row = {k.lower().strip(): v for k, v in row.items()}
                
                # Check date format
                date_val = row.get("date", "")
                try:
                    datetime.strptime(date_val, "%Y-%m-%d")
                    found_dates.add(date_val)
                except ValueError:
                    row_errors.append(f"Row {i+1}: Invalid date format '{date_val}'")
                
                # Check symbol
                symbol = row.get("symbol", "").upper()
                if symbol in EXPECTED_SYMBOLS:
                    found_symbols.add(symbol)
                
                # Check numeric fields
                for field in ["open", "high", "low", "close"]:
                    val = row.get(field, "")
                    try:
                        float_val = float(val)
                        # Check 2 decimal places
                        if "." in val and len(val.split(".")[-1]) != 2:
                            row_errors.append(f"Row {i+1}: {field} should have 2 decimal places")
                    except ValueError:
                        row_errors.append(f"Row {i+1}: Invalid {field} value '{val}'")
                
                # Check volume is integer
                vol = row.get("volume", "")
                try:
                    int(vol)
                except ValueError:
                    row_errors.append(f"Row {i+1}: Volume should be integer, got '{vol}'")
                
                if not row_errors:
                    valid_rows += 1
                elif len(scorecard["format_errors"]) < 10:  # Limit error messages
                    scorecard["format_errors"].extend(row_errors)
            
            scorecard["date_count"] = len(found_dates)
            scorecard["symbol_count"] = len(found_symbols)
            
            # Check for missing dates
            scorecard["missing_dates"] = [d for d in EXPECTED_DATES if d not in found_dates]
            scorecard["missing_symbols"] = [s for s in EXPECTED_SYMBOLS if s not in found_symbols]
            
            # Scoring
            # Dates coverage: up to 30 points
            date_coverage = len(found_dates) / len(EXPECTED_DATES)
            points += int(30 * date_coverage)
            
            # Symbols coverage: up to 15 points
            symbol_coverage = len(found_symbols) / len(EXPECTED_SYMBOLS)
            points += int(15 * symbol_coverage)
            
            # Row count: up to 20 points
            if scorecard["row_count"] >= expected_rows:
                points += 20
            else:
                row_ratio = scorecard["row_count"] / expected_rows
                points += int(20 * row_ratio)
            
            # Format correctness: up to 15 points
            if valid_rows > 0:
                format_ratio = valid_rows / len(rows)
                points += int(15 * format_ratio)
            
            scorecard["valid_rows"] = valid_rows
            scorecard["data_validation"] = {
                "expected_rows": expected_rows,
                "date_coverage": f"{date_coverage*100:.1f}%",
                "symbol_coverage": f"{symbol_coverage*100:.1f}%"
            }
            
    except Exception as e:
        scorecard["error"] = f"Failed to parse CSV: {e}"
        return scorecard
    
    scorecard["score"] = max(0, min(100, points))
    return scorecard
