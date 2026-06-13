import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class BudgetExceeded(Exception):
    pass


class BudgetTracker:
    def __init__(self, db, daily_limit: int):
        self._db = db
        self._limit = daily_limit

    def _today(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    async def consume(self, n: int = 1) -> None:
        date = self._today()
        row = await self._db.budget_get(date, self._limit)
        if row["used"] + n > row["limit_day"]:
            raise BudgetExceeded(
                f"Presupuesto diario agotado: {row['used']}/{row['limit_day']} req"
            )
        await self._db.budget_increment(date, n)
        logger.debug("API budget: %d/%d", row["used"] + n, row["limit_day"])

    async def reset(self) -> None:
        date = self._today()
        await self._db.budget_reset(date, self._limit)
        logger.info("API budget reseteado para %s", date)

    async def status(self) -> tuple[int, int]:
        date = self._today()
        row = await self._db.budget_get(date, self._limit)
        return row["used"], row["limit_day"]
