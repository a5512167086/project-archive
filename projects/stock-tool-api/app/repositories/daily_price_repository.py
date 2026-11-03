from datetime import date

import pandas as pd
from sqlalchemy import Engine, text
from sqlalchemy.dialects.postgresql import (
    insert as pg_insert,  # 引入 PostgreSQL 專用 Insert
)


class DailyPriceRepository:
    def __init__(self, engine: Engine):
        self.engine = engine

    def get_latest_date(self) -> date | None:
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT MAX(date) FROM daily_price")).scalar()
            return result

    def bulk_upsert_from_dataframe(self, df: pd.DataFrame) -> None:
        """使用 PostgreSQL ON CONFLICT DO UPDATE 進行批量覆寫 (UPSERT)"""

        # 自訂給 pandas to_sql 用的插入函式
        def postgres_upsert(table, conn, keys, data_iter):
            data = [dict(zip(keys, row)) for row in data_iter]
            if not data:
                return

            # 建立基本的 Insert 語句
            insert_stmt = pg_insert(table.table).values(data)

            # 建立 Update 字典：除了 Primary Key 之外，其他欄位發生衝突時都要更新
            update_dict = {c.name: c for c in insert_stmt.excluded if not c.primary_key}

            # 串接 ON CONFLICT DO UPDATE 語法 (以 stock_id 和 date 作為衝突判斷依據)
            upsert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=["stock_id", "date"], set_=update_dict
            )

            conn.execute(upsert_stmt)

        # 呼叫 to_sql 並套用自訂的 UPSERT 邏輯
        df.to_sql(
            name="daily_price",
            con=self.engine,
            if_exists="append",
            index=False,
            method=postgres_upsert,  # 替換為剛寫好的函式
            chunksize=2000,
        )
