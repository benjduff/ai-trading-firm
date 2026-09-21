from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from app.market_data import fetch_last_close


@dataclass
class OrderResult:
    broker_order_id: str
    status: str
    filled_price: Optional[float] = None


class BrokerClient(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def get_last_price(self, ticker: str) -> float: ...

    @abstractmethod
    def get_account_equity(self) -> float: ...

    @abstractmethod
    def place_market_order(self, ticker: str, side: str, quantity: int) -> OrderResult: ...

    @abstractmethod
    def place_stop_order(
        self, ticker: str, side: str, quantity: int, stop_price: float
    ) -> OrderResult: ...


class BrokerError(Exception):
    pass


class MockBroker(BrokerClient):
    """Simulates instant fills at the last real (Polygon) close price, against a
    fixed hypothetical equity. Used until a real IBKR paper account is wired up -
    same interface as IBKRBroker, so switching later is a one-line config change."""

    MOCK_ACCOUNT_EQUITY = 100_000.0

    @property
    def name(self) -> str:
        return "mock"

    def get_last_price(self, ticker: str) -> float:
        return fetch_last_close(ticker)

    def get_account_equity(self) -> float:
        return self.MOCK_ACCOUNT_EQUITY

    def place_market_order(self, ticker: str, side: str, quantity: int) -> OrderResult:
        price = self.get_last_price(ticker)
        return OrderResult(
            broker_order_id=f"mock-{ticker}-{side}-{quantity}",
            status="filled",
            filled_price=price,
        )

    def place_stop_order(
        self, ticker: str, side: str, quantity: int, stop_price: float
    ) -> OrderResult:
        return OrderResult(
            broker_order_id=f"mock-stop-{ticker}-{side}-{quantity}",
            status="submitted",
        )


class IBKRBroker(BrokerClient):
    """Real Interactive Brokers paper trading client via ib_async. Requires TWS or
    IB Gateway running locally with the API enabled."""

    def __init__(self, host: str, port: int, client_id: int):
        from ib_async import IB

        self._ib = IB()
        self._ib.connect(host, port, clientId=client_id, timeout=10)

    @property
    def name(self) -> str:
        return "ibkr"

    def _contract(self, ticker: str):
        from ib_async import Stock

        contract = Stock(ticker.upper(), "SMART", "USD")
        self._ib.qualifyContracts(contract)
        return contract

    def get_last_price(self, ticker: str) -> float:
        contract = self._contract(ticker)
        ticker_data = self._ib.reqMktData(contract)
        self._ib.sleep(2)
        price = ticker_data.marketPrice()
        if price != price or price <= 0:  # NaN or missing
            raise BrokerError(f"no live market price available for {ticker}")
        return price

    def get_account_equity(self) -> float:
        for item in self._ib.accountSummary():
            if item.tag == "NetLiquidation":
                return float(item.value)
        raise BrokerError("NetLiquidation not found in IBKR account summary")

    def place_market_order(self, ticker: str, side: str, quantity: int) -> OrderResult:
        from ib_async import MarketOrder

        contract = self._contract(ticker)
        order = MarketOrder(side.upper(), quantity)
        trade = self._ib.placeOrder(contract, order)
        self._ib.sleep(2)
        return OrderResult(
            broker_order_id=str(trade.order.orderId),
            status=trade.orderStatus.status,
            filled_price=trade.orderStatus.avgFillPrice or None,
        )

    def place_stop_order(
        self, ticker: str, side: str, quantity: int, stop_price: float
    ) -> OrderResult:
        from ib_async import StopOrder

        contract = self._contract(ticker)
        order = StopOrder(side.upper(), quantity, stop_price)
        trade = self._ib.placeOrder(contract, order)
        self._ib.sleep(1)
        return OrderResult(
            broker_order_id=str(trade.order.orderId),
            status=trade.orderStatus.status,
        )


def get_broker() -> BrokerClient:
    from app.config import settings

    if settings.broker_backend == "mock":
        return MockBroker()
    return IBKRBroker(
        host=settings.ibkr_host,
        port=settings.ibkr_port,
        client_id=settings.ibkr_client_id,
    )
