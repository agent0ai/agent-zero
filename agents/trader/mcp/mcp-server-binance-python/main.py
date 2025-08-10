import os
from typing import Optional, Literal, Any, Dict, Annotated
from contextlib import asynccontextmanager

from fastmcp.server import FastMCP, Context
from binance.async_client import AsyncClient
from binance.exceptions import BinanceAPIException, BinanceRequestException
from pydantic import Field


API_KEY_ENV = "BINANCE_API_KEY"
API_SECRET_ENV = "BINANCE_API_SECRET"
TESTNET_ENV = "BINANCE_TESTNET"


async def _create_client() -> AsyncClient:
    api_key = os.getenv(API_KEY_ENV)
    api_secret = os.getenv(API_SECRET_ENV)
    if not api_key or not api_secret:
        raise RuntimeError(
            f"Missing Binance API credentials. Set {API_KEY_ENV} and {API_SECRET_ENV} in environment."
        )

    testnet = os.getenv(TESTNET_ENV, "false").lower() in {"1", "true", "yes", "on"}
    client = await AsyncClient.create(api_key=api_key, api_secret=api_secret, testnet=testnet)
    return client


def ensure_content(result: Any) -> Any:
    """Wrap lists so MCP content is never empty.

    MCP drops empty lists as empty tool output. This ensures we always return a
    serializable object even when the API returns an empty list.
    """
    if isinstance(result, (list, tuple)):
        return {"items": list(result), "count": len(result)}
    return result


@asynccontextmanager
async def lifespan(app: FastMCP):
    client: AsyncClient | None = None
    try:
        client = await _create_client()
        # attach for access from tools via ctx.fastmcp
        setattr(app, "binance_client", client)
        yield {"binance_client": client}
    finally:
        if client is not None:
            await client.close_connection()


mcp = FastMCP(
    name="binance-mcp-python",
    instructions=(
        "MCP server exposing Binance Spot REST market data retrieval and order management via python-binance."
    ),
    lifespan=lifespan,
    dependencies=["python-binance"],
)


# --- Market Data Tools ---


@mcp.tool(
    name="binance_get_exchange_info",
    description="Get exchange trading rules and symbol information.",
    tags={"market-data"},
)
async def binance_get_exchange_info(
    ctx: Context,
    symbol: Annotated[Optional[str], Field(description="Optional trading pair symbol to filter results, e.g. 'BTCUSDT'.")] = None,
) -> Dict[str, Any]:
    """
    Retrieve the full exchange information (symbols, filters, rate limits) and optionally filter to one symbol.

    Parameters:
    - ctx: FastMCP context (injected automatically)
    - symbol: Optional trading pair, e.g. "BTCUSDT". If provided, only that symbol's info is returned.

    Returns:
    - JSON dict containing exchange info (rate limits, server timezone, list of symbol objects).

    Notes:
    - Source: Binance Spot REST `GET /api/v3/exchangeInfo`.

    Example:
    - Get all symbols: call with no symbol.
    - Get single symbol: symbol="BTCUSDT".
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        info = await client.get_exchange_info()
        if symbol:
            data = info
            try:
                symbols_list = data.get("symbols", []) if isinstance(data, dict) else []
                filtered = [s for s in symbols_list if s.get("symbol") == symbol]
                data["symbols"] = filtered
                return ensure_content(data)
            except Exception:
                return ensure_content(info)
        return ensure_content(info)
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


@mcp.tool(
    name="binance_get_order_book",
    description="Get current order book (depth) for a symbol.",
    tags={"market-data", "orderbook"},
)
async def binance_get_order_book(
    symbol: Annotated[str, Field(description="Trading pair symbol, e.g. 'BTCUSDT'.")],
    ctx: Context,
    limit: Annotated[Optional[int], Field(description="Depth size. Common values: 5, 10, 20, 50, 100, 500, 1000, 5000.")] = None,
) -> Dict[str, Any]:
    """
    Fetch the order book bids/asks for a trading symbol.

    Parameters:
    - symbol: Trading symbol like "BTCUSDT".
    - ctx: FastMCP context.
    - limit: Optional depth size (default exchange value if omitted).

    Returns:
    - JSON dict with keys: lastUpdateId, bids, asks.

    Notes:
    - Source: Binance Spot REST `GET /api/v3/depth`.
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        resp = await client.get_order_book(symbol=symbol, limit=limit)
        return ensure_content(resp)
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


@mcp.tool(
    name="binance_get_recent_trades",
    description="Get most recent trades for a symbol.",
    tags={"market-data", "trades"},
)
async def binance_get_recent_trades(
    symbol: Annotated[str, Field(description="Trading pair symbol, e.g. 'BTCUSDT'.")],
    ctx: Context,
    limit: Annotated[Optional[int], Field(description="Max number of trades to return (default 500, max 1000).")]= None,
) -> Any:
    """
    Retrieve recent trades for a symbol (most recent first).

    Parameters:
    - symbol: Trading symbol like "BTCUSDT".
    - ctx: FastMCP context.
    - limit: Optional number of trades to fetch.

    Returns:
    - List of trade objects (id, price, qty, time, isBuyerMaker, etc.).

    Notes:
    - Source: Binance Spot REST `GET /api/v3/trades`.
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        resp = await client.get_recent_trades(symbol=symbol, limit=limit)
        return ensure_content(resp)
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


@mcp.tool(
    name="binance_get_historical_trades",
    description="Get older market trades for a symbol (requires API key).",
    tags={"market-data", "trades"},
)
async def binance_get_historical_trades(
    symbol: Annotated[str, Field(description="Trading pair symbol, e.g. 'BTCUSDT'.")],
    ctx: Context,
    limit: Annotated[Optional[int], Field(description="Max number of trades to return (default 500, max 1000).")]= None,
    fromId: Annotated[Optional[int], Field(description="Trade id to fetch from. If omitted, most recent trades are returned.")] = None,
) -> Any:
    """
    Retrieve older trades for a symbol, starting from a given trade id.

    Parameters:
    - symbol: Trading symbol like "BTCUSDT".
    - ctx: FastMCP context.
    - limit: Optional number of trades to fetch.
    - fromId: Optional trade id to start from.

    Returns:
    - List of trade objects.

    Notes:
    - Source: Binance Spot REST `GET /api/v3/historicalTrades`.
    - Requires API key permissions.
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        resp = await client.get_historical_trades(symbol=symbol, limit=limit, fromId=fromId)
        return ensure_content(resp)
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


@mcp.tool(
    name="binance_get_aggregate_trades",
    description="Get compressed, aggregate trades list for a symbol.",
    tags={"market-data", "trades"},
)
async def binance_get_aggregate_trades(
    symbol: Annotated[str, Field(description="Trading pair symbol, e.g. 'BTCUSDT'.")],
    ctx: Context,
    fromId: Annotated[Optional[int], Field(description="Aggregate trade id to fetch from.")] = None,
    startTime: Annotated[Optional[int], Field(description="Start time in ms since epoch.")] = None,
    endTime: Annotated[Optional[int], Field(description="End time in ms since epoch.")] = None,
    limit: Annotated[Optional[int], Field(description="Max results (default 500, max 1000).")]= None,
) -> Any:
    """
    Retrieve aggregate trades for a symbol over an optional time/id window.

    Parameters:
    - symbol: Trading symbol like "BTCUSDT".
    - ctx: FastMCP context.
    - fromId: Optional aggregate trade id to start from.
    - startTime/endTime: Optional time window in milliseconds.
    - limit: Optional maximum results.

    Returns:
    - List of aggregate trades.

    Notes:
    - Source: Binance Spot REST `GET /api/v3/aggTrades`.
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        resp = await client.get_aggregate_trades(
            symbol=symbol,
            fromId=fromId,
            startTime=startTime,
            endTime=endTime,
            limit=limit,
        )
        return ensure_content(resp)
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


@mcp.tool(
    name="binance_get_klines",
    description="Get Kline/candlestick bars for a symbol and interval.",
    tags={"market-data", "klines"},
)
async def binance_get_klines(
    symbol: Annotated[str, Field(description="Trading pair symbol, e.g. 'BTCUSDT'.")],
    interval: Annotated[str, Field(description="Kline interval, e.g. '1m', '5m', '1h', '1d'.")],
    ctx: Context,
    startTime: Annotated[Optional[int], Field(description="Start time in ms since epoch.")] = None,
    endTime: Annotated[Optional[int], Field(description="End time in ms since epoch.")] = None,
    limit: Annotated[Optional[int], Field(description="Number of klines to return (default 500, max 1000).")]= None,
) -> Any:
    """
    Retrieve OHLCV candlesticks for a symbol.

    Parameters:
    - symbol: Trading symbol like "BTCUSDT".
    - interval: Kline interval string (e.g., "1m", "1h", "1d").
    - ctx: FastMCP context.
    - startTime/endTime: Optional time window in milliseconds.
    - limit: Optional maximum number of klines.

    Returns:
    - List of klines: [ openTime, open, high, low, close, volume, closeTime, ... ].

    Notes:
    - Source: Binance Spot REST `GET /api/v3/klines`.
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        resp = await client.get_klines(
            symbol=symbol,
            interval=interval,
            startTime=startTime,
            endTime=endTime,
            limit=limit,
        )
        return ensure_content(resp)
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


@mcp.tool(
    name="binance_get_avg_price",
    description="Get current average price for a symbol.",
    tags={"market-data", "price"},
)
async def binance_get_avg_price(
    symbol: Annotated[str, Field(description="Trading pair symbol, e.g. 'BTCUSDT'.")],
    ctx: Context,
) -> Any:
    """
    Retrieve the weighted average price for the past 5 minutes for a symbol.

    Parameters:
    - symbol: Trading symbol like "BTCUSDT".
    - ctx: FastMCP context.

    Returns:
    - JSON object with averaged price information.

    Notes:
    - Source: Binance Spot REST `GET /api/v3/avgPrice`.
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        resp = await client.get_avg_price(symbol=symbol)
        return ensure_content(resp)
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


@mcp.tool(
    name="binance_get_ticker_24hr",
    description="Get 24hr rolling window price change statistics.",
    tags={"market-data", "ticker"},
)
async def binance_get_ticker_24hr(
    ctx: Context,
    symbol: Annotated[Optional[str], Field(description="Optional trading symbol to fetch stats for a single pair.")] = None,
) -> Any:
    """
    Retrieve 24h price change statistics. If no symbol is provided, returns data for all symbols.

    Parameters:
    - ctx: FastMCP context.
    - symbol: Optional trading symbol like "BTCUSDT".

    Returns:
    - JSON object (or list) with 24h ticker statistics (price change, percent, high/low, volumes).

    Notes:
    - Source: Binance Spot REST `GET /api/v3/ticker/24hr`.
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        resp = await client.get_ticker(symbol=symbol)
        return ensure_content(resp)
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


@mcp.tool(
    name="binance_get_symbol_ticker_price",
    description="Get the latest price for a symbol (or all symbols).",
    tags={"market-data", "price"},
)
async def binance_get_symbol_ticker_price(
    ctx: Context,
    symbol: Annotated[Optional[str], Field(description="Optional trading symbol like 'BTCUSDT'.")]= None,
) -> Any:
    """
    Retrieve the latest price for a specific symbol or all symbols.

    Parameters:
    - ctx: FastMCP context.
    - symbol: Optional trading symbol like "BTCUSDT".

    Returns:
    - JSON object or list with latest price(s).

    Notes:
    - Source: Binance Spot REST `GET /api/v3/ticker/price`.
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        resp = await client.get_symbol_ticker(symbol=symbol)
        return ensure_content(resp)
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


@mcp.tool(
    name="binance_get_book_ticker",
    description="Best bid/ask (book ticker) for a symbol or all symbols.",
    tags={"market-data", "orderbook"},
)
async def binance_get_book_ticker(
    ctx: Context,
    symbol: Annotated[Optional[str], Field(description="Optional trading symbol like 'BTCUSDT'.")]= None,
) -> Any:
    """
    Retrieve best bid/ask on the order book for a symbol or all symbols.

    Parameters:
    - ctx: FastMCP context.
    - symbol: Optional trading symbol like "BTCUSDT".

    Returns:
    - JSON object or list with best bid/ask prices and quantities.

    Notes:
    - Source: Binance Spot REST `GET /api/v3/ticker/bookTicker`.
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        resp = await client.get_orderbook_ticker(symbol=symbol)
        return ensure_content(resp)
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


# --- Order Management Tools ---


@mcp.tool(
    name="binance_place_order",
    description=(
        "Place a new spot order. For LIMIT orders, provide price and timeInForce. "
        "Use quantity or quoteOrderQty. Set test=true to validate without execution."
    ),
    tags={"orders"},
)
async def binance_place_order(
    symbol: Annotated[str, Field(description="Trading pair symbol, e.g. 'BTCUSDT'.")],
    side: Annotated[Literal["BUY", "SELL"], Field(description="Order side: BUY or SELL.")],
    type: Annotated[
        Literal[
            "LIMIT",
            "MARKET",
            "STOP_LOSS",
            "STOP_LOSS_LIMIT",
            "TAKE_PROFIT",
            "TAKE_PROFIT_LIMIT",
            "LIMIT_MAKER",
        ],
        Field(description="Order type per Binance Spot API."),
    ],
    ctx: Context,
    quantity: Annotated[Optional[float], Field(description="Base asset quantity. Required for many order types.")] = None,
    quoteOrderQty: Annotated[Optional[float], Field(description="Quote asset quantity for MARKET orders.")] = None,
    price: Annotated[Optional[float], Field(description="Price for LIMIT orders.")] = None,
    timeInForce: Annotated[Optional[Literal["GTC", "IOC", "FOK"]], Field(description="Required for LIMIT/STOP_LIMIT/TAKE_PROFIT_LIMIT.")] = None,
    newClientOrderId: Annotated[Optional[str], Field(description="User-defined id for the order.")] = None,
    stopPrice: Annotated[Optional[float], Field(description="Stop price for STOP/TAKE_PROFIT variants.")] = None,
    icebergQty: Annotated[Optional[float], Field(description="Iceberg quantity (if supported).")] = None,
    newOrderRespType: Annotated[Optional[Literal["ACK", "RESULT", "FULL"]], Field(description="Response detail level. Default RESULT.")] = None,
    recvWindow: Annotated[Optional[int], Field(description="Request validity window in ms (<=60000).")]= None,
    test: Annotated[bool, Field(description="If true, validate without placing the order (create_test_order).")]= False,
) -> Any:
    """
    Place a new spot order.

    Parameters:
    - symbol: Trading symbol.
    - side: BUY or SELL.
    - type: Order type.
    - ctx: FastMCP context.
    - quantity/quoteOrderQty: Provide exactly one for MARKET orders (per Binance rules).
    - price/timeInForce: Required for LIMIT-type orders.
    - stopPrice: Required for STOP/TAKE_PROFIT variants.
    - newOrderRespType: ACK | RESULT | FULL.
    - recvWindow: Optional request validity in ms.
    - test: If true, call create_test_order (no execution).

    Returns:
    - JSON result of the order placement (or test validation response).

    Notes:
    - Source: Binance Spot REST `POST /api/v3/order` and `POST /api/v3/order/test`.
    - Ensure lot size and price filters are respected (use exchange info to validate).
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        args = dict(
            symbol=symbol,
            side=side,
            type=type,
            quantity=quantity,
            quoteOrderQty=quoteOrderQty,
            price=price,
            timeInForce=timeInForce,
            newClientOrderId=newClientOrderId,
            stopPrice=stopPrice,
            icebergQty=icebergQty,
            newOrderRespType=newOrderRespType,
            recvWindow=recvWindow,
        )
        args = {k: v for k, v in args.items() if v is not None}
        if test:
            resp = await client.create_test_order(**args)
            return ensure_content(resp)
        resp = await client.create_order(**args)
        return ensure_content(resp)
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


@mcp.tool(
    name="binance_get_order",
    description="Get an order's status by orderId or origClientOrderId.",
    tags={"orders"},
)
async def binance_get_order(
    symbol: Annotated[str, Field(description="Trading pair symbol, e.g. 'BTCUSDT'.")],
    ctx: Context,
    orderId: Annotated[Optional[int], Field(description="Exchange-assigned order id.")] = None,
    origClientOrderId: Annotated[Optional[str], Field(description="User-defined client order id.")] = None,
    recvWindow: Annotated[Optional[int], Field(description="Request validity window in ms (<=60000).")]= None,
) -> Any:
    """
    Query the current status/details of a specific order.

    Parameters:
    - symbol: Trading symbol like "BTCUSDT".
    - ctx: FastMCP context.
    - orderId or origClientOrderId: Provide one identifier.
    - recvWindow: Optional request validity in ms.

    Returns:
    - JSON object with order details/status.

    Notes:
    - Source: Binance Spot REST `GET /api/v3/order`.
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        resp = await client.get_order(
            symbol=symbol,
            orderId=orderId,
            origClientOrderId=origClientOrderId,
            recvWindow=recvWindow,
        )
        return ensure_content(resp)
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


@mcp.tool(
    name="binance_cancel_order",
    description="Cancel a specific active order.",
    tags={"orders"},
)
async def binance_cancel_order(
    symbol: Annotated[str, Field(description="Trading pair symbol, e.g. 'BTCUSDT'.")],
    ctx: Context,
    orderId: Annotated[Optional[int], Field(description="Exchange-assigned order id.")] = None,
    origClientOrderId: Annotated[Optional[str], Field(description="User-defined client order id.")] = None,
    newClientOrderId: Annotated[Optional[str], Field(description="New client order id to replace the canceled one.")] = None,
    recvWindow: Annotated[Optional[int], Field(description="Request validity window in ms (<=60000).")]= None,
) -> Any:
    """
    Cancel a live order by id or origClientOrderId.

    Parameters:
    - symbol: Trading symbol like "BTCUSDT".
    - ctx: FastMCP context.
    - orderId/origClientOrderId: Identify the order to cancel.
    - newClientOrderId: Optional replacement id.
    - recvWindow: Optional request validity in ms.

    Returns:
    - JSON object describing the canceled order.

    Notes:
    - Source: Binance Spot REST `DELETE /api/v3/order`.
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        resp = await client.cancel_order(
            symbol=symbol,
            orderId=orderId,
            origClientOrderId=origClientOrderId,
            newClientOrderId=newClientOrderId,
            recvWindow=recvWindow,
        )
        return ensure_content(resp)
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


@mcp.tool(
    name="binance_cancel_open_orders",
    description="Cancel all open orders on a symbol.",
    tags={"orders"},
)
async def binance_cancel_open_orders(
    symbol: Annotated[str, Field(description="Trading pair symbol, e.g. 'BTCUSDT'.")],
    ctx: Context,
    recvWindow: Annotated[Optional[int], Field(description="Request validity window in ms (<=60000).")]= None,
) -> Any:
    """
    Cancel all currently open orders for a symbol.

    Parameters:
    - symbol: Trading symbol like "BTCUSDT".
    - ctx: FastMCP context.
    - recvWindow: Optional request validity in ms.

    Returns:
    - JSON array describing results of cancel operations.

    Notes:
    - Source: Binance Spot REST `DELETE /api/v3/openOrders`.
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        resp = await client.v3_delete_open_orders(symbol=symbol, recvWindow=recvWindow)
        return ensure_content(resp)
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


@mcp.tool(
    name="binance_get_open_orders",
    description="Get all open orders; optionally filter by symbol.",
    tags={"orders"},
)
async def binance_get_open_orders(
    ctx: Context,
    symbol: Annotated[Optional[str], Field(description="Optional trading symbol to filter results.")] = None,
    recvWindow: Annotated[Optional[int], Field(description="Request validity window in ms (<=60000).")]= None,
) -> Any:
    """
    List all open orders. If a symbol is provided, returns open orders only for that symbol.

    Parameters:
    - ctx: FastMCP context.
    - symbol: Optional trading symbol like "BTCUSDT".
    - recvWindow: Optional request validity in ms.

    Returns:
    - JSON list of open orders.

    Notes:
    - Source: Binance Spot REST `GET /api/v3/openOrders`.
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        resp = await client.get_open_orders(symbol=symbol, recvWindow=recvWindow)
        return ensure_content(resp)
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


@mcp.tool(
    name="binance_get_all_orders",
    description="Get all account orders (active, canceled, filled) for a symbol.",
    tags={"orders"},
)
async def binance_get_all_orders(
    symbol: Annotated[str, Field(description="Trading pair symbol, e.g. 'BTCUSDT'.")],
    ctx: Context,
    orderId: Annotated[Optional[int], Field(description="Order id to return results from.")] = None,
    startTime: Annotated[Optional[int], Field(description="Start time (ms).")] = None,
    endTime: Annotated[Optional[int], Field(description="End time (ms).")] = None,
    limit: Annotated[Optional[int], Field(description="Number of orders to return (default 500, max 1000).")]= None,
    recvWindow: Annotated[Optional[int], Field(description="Request validity window in ms (<=60000).")]= None,
) -> Any:
    """
    Retrieve historical orders for a symbol across all statuses.

    Parameters:
    - symbol: Trading symbol like "BTCUSDT".
    - ctx: FastMCP context.
    - orderId: Return results from this order id.
    - startTime/endTime: Optional time range in ms.
    - limit: Optional maximum number of orders.
    - recvWindow: Optional request validity in ms.

    Returns:
    - JSON list of order objects.

    Notes:
    - Source: Binance Spot REST `GET /api/v3/allOrders`.
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        resp = await client.get_all_orders(
            symbol=symbol,
            orderId=orderId,
            startTime=startTime,
            endTime=endTime,
            limit=limit,
            recvWindow=recvWindow,
        )
        return ensure_content(resp)
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


@mcp.tool(
    name="binance_account_info",
    description="Get current account information (balances, permissions, etc.).",
    tags={"account"},
)
async def binance_account_info(
    ctx: Context,
    recvWindow: Annotated[Optional[int], Field(description="Request validity window in ms (<=60000).")]= None,
) -> Any:
    """
    Retrieve current account information (balances, maker/taker commissions, permissions).

    Parameters:
    - ctx: FastMCP context.
    - recvWindow: Optional request validity in ms.

    Returns:
    - JSON object with account data and balances.

    Notes:
    - Source: Binance Spot REST `GET /api/v3/account`.
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        resp = await client.get_account(recvWindow=recvWindow)
        return ensure_content(resp)
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


@mcp.tool(
    name="binance_asset_balance",
    description="Get balance for a single asset.",
    tags={"account"},
)
async def binance_asset_balance(
    asset: Annotated[str, Field(description="Asset symbol, e.g. 'BTC', 'USDT'.")],
    ctx: Context,
    recvWindow: Annotated[Optional[int], Field(description="Request validity window in ms (<=60000).")]= None,
) -> Any:
    """
    Retrieve balance information for a specific asset.

    Parameters:
    - asset: Asset code like "BTC", "USDT".
    - ctx: FastMCP context.
    - recvWindow: Optional request validity in ms.

    Returns:
    - JSON object with asset free/locked balances.

    Notes:
    - Source: Binance Spot REST `GET /api/v3/account` (parsed by client helper).
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        resp = await client.get_asset_balance(asset=asset, recvWindow=recvWindow)
        return ensure_content(resp)
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


# OCO Orders
@mcp.tool(
    name="binance_create_oco_order",
    description="Place a new OCO (One-Cancels-the-Other) order.",
    tags={"orders", "oco"},
)
async def binance_create_oco_order(
    symbol: Annotated[str, Field(description="Trading pair symbol, e.g. 'BTCUSDT'.")],
    side: Annotated[Literal["BUY", "SELL"], Field(description="Order side: BUY or SELL.")],
    quantity: Annotated[float, Field(description="Base asset quantity.")],
    price: Annotated[float, Field(description="Limit price for the limit leg.")],
    stopPrice: Annotated[float, Field(description="Stop price for the stop leg.")],
    ctx: Context,
    listClientOrderId: Annotated[Optional[str], Field(description="Client id for the OCO list.")] = None,
    limitClientOrderId: Annotated[Optional[str], Field(description="Client id for the limit leg.")] = None,
    limitIcebergQty: Annotated[Optional[float], Field(description="Iceberg qty for the limit leg.")] = None,
    stopClientOrderId: Annotated[Optional[str], Field(description="Client id for the stop leg.")] = None,
    stopLimitPrice: Annotated[Optional[float], Field(description="Limit price for STOP_LIMIT variant.")] = None,
    stopIcebergQty: Annotated[Optional[float], Field(description="Iceberg qty for the stop leg.")] = None,
    stopLimitTimeInForce: Annotated[Optional[Literal["GTC", "IOC", "FOK"]], Field(description="TimeInForce for stop-limit leg.")] = None,
    newOrderRespType: Annotated[Optional[Literal["ACK", "RESULT", "FULL"]], Field(description="Response detail level.")] = None,
    recvWindow: Annotated[Optional[int], Field(description="Request validity window in ms (<=60000).")]= None,
) -> Any:
    """
    Place an OCO order with limit and stop legs.

    Parameters:
    - symbol: Trading symbol.
    - side: BUY or SELL.
    - quantity: Base asset quantity.
    - price: Limit price for the limit leg.
    - stopPrice: Stop price for the stop leg.
    - ctx: FastMCP context.
    - Additional client ids and iceberg/timeInForce fields are optional as per Binance OCO specs.

    Returns:
    - JSON object describing the created OCO order list and its legs.

    Notes:
    - Source: Binance Spot REST `POST /api/v3/order/oco`.
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        args = dict(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            stopPrice=stopPrice,
            listClientOrderId=listClientOrderId,
            limitClientOrderId=limitClientOrderId,
            limitIcebergQty=limitIcebergQty,
            stopClientOrderId=stopClientOrderId,
            stopLimitPrice=stopLimitPrice,
            stopIcebergQty=stopIcebergQty,
            stopLimitTimeInForce=stopLimitTimeInForce,
            newOrderRespType=newOrderRespType,
            recvWindow=recvWindow,
        )
        args = {k: v for k, v in args.items() if v is not None}
        resp = await client.create_oco_order(**args)
        return ensure_content(resp)
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


@mcp.tool(
    name="binance_cancel_oco_order",
    description="Cancel an existing OCO order by orderListId or listClientOrderId.",
    tags={"orders", "oco"},
)
async def binance_cancel_oco_order(
    symbol: Annotated[str, Field(description="Trading pair symbol, e.g. 'BTCUSDT'.")],
    ctx: Context,
    orderListId: Annotated[Optional[int], Field(description="OCO orderListId to cancel.")] = None,
    listClientOrderId: Annotated[Optional[str], Field(description="Client order id of the OCO list.")] = None,
    newClientOrderId: Annotated[Optional[str], Field(description="New client id for the canceled OCO.")] = None,
    recvWindow: Annotated[Optional[int], Field(description="Request validity window in ms (<=60000).")]= None,
) -> Any:
    """
    Cancel an OCO order (order list) by id or client id.

    Parameters:
    - symbol: Trading symbol like "BTCUSDT".
    - ctx: FastMCP context.
    - orderListId or listClientOrderId: Provide one to identify the OCO list.
    - newClientOrderId: Optional replacement id.
    - recvWindow: Optional request validity in ms.

    Returns:
    - JSON object describing the cancellation.

    Notes:
    - Source: Binance Spot REST `DELETE /api/v3/orderList`.
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        resp = await client.v3_delete_order_list(
            symbol=symbol,
            orderListId=orderListId,
            listClientOrderId=listClientOrderId,
            newClientOrderId=newClientOrderId,
            recvWindow=recvWindow,
        )
        return ensure_content(resp)
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


@mcp.tool(
    name="binance_get_oco_order",
    description="Get an OCO order list by orderListId or listClientOrderId.",
    tags={"orders", "oco"},
)
async def binance_get_oco_order(
    ctx: Context,
    orderListId: Annotated[Optional[int], Field(description="OCO orderListId to fetch.")] = None,
    listClientOrderId: Annotated[Optional[str], Field(description="Client order id of the OCO list.")] = None,
) -> Any:
    """
    Fetch an OCO order list details by id or client id.

    Parameters:
    - ctx: FastMCP context.
    - orderListId or listClientOrderId: Provide one identifier.

    Returns:
    - JSON object describing the OCO order list and legs.

    Notes:
    - Source: Binance Spot REST `GET /api/v3/orderList`.
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        if orderListId is not None:
            resp = await client.v3_get_order_list(orderListId=orderListId)
            return ensure_content(resp)
        if listClientOrderId is not None:
            resp = await client.v3_get_order_list(origClientOrderId=listClientOrderId)
            return ensure_content(resp)
        return {"error": "Provide orderListId or listClientOrderId"}
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


@mcp.tool(
    name="binance_get_open_oco_orders",
    description="List all currently open OCO orders.",
    tags={"orders", "oco"},
)
async def binance_get_open_oco_orders(
    ctx: Context,
    recvWindow: Annotated[Optional[int], Field(description="Request validity window in ms (<=60000).")]= None,
) -> Any:
    """
    Retrieve all currently open OCO order lists.

    Parameters:
    - ctx: FastMCP context.
    - recvWindow: Optional request validity in ms.

    Returns:
    - JSON list of open OCO order lists.

    Notes:
    - Source: Binance Spot REST `GET /api/v3/openOrderList`.
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        resp = await client.get_open_oco_orders(recvWindow=recvWindow)
        return ensure_content(resp)
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


@mcp.tool(
    name="binance_get_all_oco_orders",
    description="List all OCO orders with optional pagination/time filters.",
    tags={"orders", "oco"},
)
async def binance_get_all_oco_orders(
    ctx: Context,
    fromId: Annotated[Optional[int], Field(description="Return results from this orderListId.")] = None,
    startTime: Annotated[Optional[int], Field(description="Start time (ms).")] = None,
    endTime: Annotated[Optional[int], Field(description="End time (ms).")] = None,
    limit: Annotated[Optional[int], Field(description="Max results (default 500, max 1000).")]= None,
    recvWindow: Annotated[Optional[int], Field(description="Request validity window in ms (<=60000).")]= None,
) -> Any:
    """
    Retrieve historical OCO order lists.

    Parameters:
    - ctx: FastMCP context.
    - fromId: Return results from this orderListId.
    - startTime/endTime: Optional time range in ms.
    - limit: Optional maximum results.
    - recvWindow: Optional request validity in ms.

    Returns:
    - JSON list of OCO order lists.

    Notes:
    - Source: Binance Spot REST `GET /api/v3/allOrderList`.
    """
    client: AsyncClient = getattr(ctx.fastmcp, "binance_client")
    try:
        params: Dict[str, Any] = {}
        if fromId is not None:
            params["fromId"] = fromId
        if startTime is not None:
            params["startTime"] = startTime
        if endTime is not None:
            params["endTime"] = endTime
        if limit is not None:
            params["limit"] = limit
        if recvWindow is not None:
            params["recvWindow"] = recvWindow
        resp = await client.v3_get_all_order_list(**params)
        return ensure_content(resp)
    except (BinanceAPIException, BinanceRequestException) as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Default to stdio transport when run directly
    mcp.run(transport="stdio")
