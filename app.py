from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from enum import Enum
import yfinance as yf
import pandas as pd
import numpy as np

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_methods = ["POST"],
    allow_headers = ["*"],
)

class ColumnEnum(str, Enum):
    Open = "Open"
    High = "High"
    Low = "Low"
    Close = "Close"
    Volume = "Volume"

class TimeFrame(BaseModel):
    start_date: str
    end_date: str

class StockRequest(BaseModel):
    timeframe: TimeFrame
    symbol_list: list[str]
    column: ColumnEnum

class StockPrice:
    def __init__(self, request_data: StockRequest):
        self.start_date = request_data.timeframe.start_date
        self.end_date = request_data.timeframe.end_date
        self.symbol_list = request_data.symbol_list
        self.column = request_data.column
        self.data_frame = self._get_stock_price()
        self.result_list = self._prepare_data()

    def _get_stock_price(self):
        stocks = yf.download(self.symbol_list, start = self.start_date, end = self.end_date)
        column_name = self.column.value
        df = stocks[column_name].iloc[::-1].replace(np.nan, None)  
        if isinstance(df, pd.Series): 
            df = df.to_frame(name=self.symbol_list[0])
        return df

    def _prepare_data(self):
        return [
            {
                "time": index.strftime("%Y-%m-%d"),
                "data": [{"symbol": symbol, "value": value} for symbol, value in row.items()]
            }
            for index, row in self.data_frame.iterrows()
        ]

    def get_result(self):
        return {
            "status": 1,
            "result": self.result_list
        }

@app.post("/stock", summary = "Retrieve stock price data", description = "Fetch stock prices for specific symbols and time range.")
async def stock(request_data: StockRequest):
    try:
        stock_price = StockPrice(request_data)
        return stock_price.get_result()
    except Exception as e:
        raise HTTPException(status_code = 400, detail = str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host = "0.0.0.0", port = 2949, reload = True)
