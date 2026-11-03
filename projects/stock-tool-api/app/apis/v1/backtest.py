from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_backtest_service
from app.services.backtest_service import BacktestService

router = APIRouter()


@router.get("/sma/{ticker}")
def run_sma_backtest(
    ticker: str,
    fast: int = 20,
    slow: int = 60,
    service: BacktestService = Depends(get_backtest_service),
):
    result = service.run_sma_crossover_strategy(
        ticker,
        fast_period=fast,
        slow_period=slow,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
