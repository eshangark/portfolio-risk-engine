"""Market-data contract, bounded Alpaca reads and calendar-aware preparation.

No trading endpoints. All network access is injectable for reproducible tests.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from collections import OrderedDict
from copy import deepcopy
from typing import Protocol
import hashlib
import json
import re
import time
import numpy as np
import pandas as pd
import requests
import exchange_calendars as xcals

class DataError(ValueError):
    """An actionable data/entitlement/coverage failure with no credentials attached."""

@dataclass(frozen=True)
class History:
    symbols: tuple[str, ...]
    bars: dict
    feed: str
    adjustment: str
    retrieved_at: str
    refresh: dict | None = None

@dataclass(frozen=True)
class Prepared:
    returns: pd.DataFrame
    expected_sessions: int
    dropped_return_dates: tuple[str, ...]
    latest_session: str
    identity: str
    metadata: dict

class MarketData(Protocol):
    def history(self, symbols, start, end) -> History: ...
    def latest_prices(self, symbols, now=None) -> dict: ...


def symbols_checked(symbols):
    symbols=tuple(str(s).strip().upper() for s in symbols)
    if not symbols or len(symbols)>50 or len(set(symbols))!=len(symbols):
        raise DataError('Enter 1–50 unique symbols.')
    if any(re.fullmatch(r'[A-Z][A-Z0-9.\-]{0,9}',s) is None for s in symbols):
        raise DataError('Unsupported symbol syntax.')
    return symbols


def utc(value):
    stamp=pd.Timestamp(value)
    if pd.isna(stamp) or stamp.tzinfo is None: raise DataError('A valid timestamp with an explicit timezone is required.')
    return stamp.tz_convert('UTC')


def snapshot_changes(previous, current):
    """Audit complete provider snapshots; never splice adjustment vintages."""
    def indexed(bars):
        result={}
        for symbol, rows in bars.items():
            for row in rows:
                if not isinstance(row,dict): raise DataError('Malformed daily bar.')
                try: key=(symbol,utc(row['t']).isoformat())
                except (KeyError,TypeError,ValueError): raise DataError('Malformed bar timestamp.') from None
                if key in result: raise DataError('Duplicate bar timestamp.')
                result[key]=row
        return result
    old=indexed(previous); new=indexed(current)
    return {'added':len(new.keys()-old.keys()), 'removed':len(old.keys()-new.keys()),
            'revised':sum(old[k]!=new[k] for k in old.keys()&new.keys()),
            'policy':'complete adjusted snapshot audit; no mixed vintages'}


def completed_history_end(now):
    """Conservative endpoint cutoff compatible with delayed-feed history access."""
    return utc(now)-pd.Timedelta(minutes=15)


class AlpacaData:
    BASE='https://data.alpaca.markets'
    def __init__(self,key,secret,feed='iex',session=None,sleep=time.sleep,clock=time.time,cache_ttl=900):
        if not key or not secret: raise DataError('Set ALPACA_API_KEY and ALPACA_API_SECRET in server secrets.')
        if feed not in ('iex','sip'): raise DataError('Choose IEX or SIP explicitly.')
        self._headers={'APCA-API-KEY-ID':key,'APCA-API-SECRET-KEY':secret}
        self.feed=feed; self._session=session or requests.Session(); self._sleep=sleep; self._clock=clock
        self._cache=OrderedDict(); self._ttl=cache_ttl

    def _get(self,path,params):
        for attempt in range(4):
            try:
                response=self._session.get(self.BASE+path,params=params,headers=self._headers,timeout=20)
            except requests.RequestException:
                if attempt==3: raise DataError('Market-data connection failed after bounded retries.') from None
                self._sleep(2**attempt); continue
            if response.status_code==429 or 500<=response.status_code<600:
                if attempt==3: raise DataError('Market-data service is rate-limited or unavailable.')
                try: delay=float(response.headers.get('Retry-After',2**attempt))
                except (TypeError,ValueError): delay=2**attempt
                if not np.isfinite(delay): delay=2**attempt
                self._sleep(max(0,min(30,delay))); continue
            if response.status_code in (401,403): raise DataError('Credentials or requested feed entitlement were rejected.')
            if response.status_code!=200: raise DataError(f'Market-data request failed (HTTP {response.status_code}).')
            try: payload=response.json()
            except ValueError: raise DataError('Provider returned malformed JSON.') from None
            if not isinstance(payload,dict): raise DataError('Provider returned an invalid response shape.')
            return payload
        raise DataError('Request exhausted.')

    def history(self,symbols,start,end,adjustment='all',force_refresh=False):
        symbols=symbols_checked(symbols); start=utc(start); end=utc(end)
        if start>=end: raise DataError('History start must precede end.')
        if adjustment not in ('raw','split','dividend','all'): raise DataError('Unsupported adjustment mode.')
        key=(symbols,start.isoformat(),end.isoformat(),self.feed,adjustment)
        cached=self._cache.get(key)
        if cached and not force_refresh and self._clock()-cached[0]<self._ttl: return deepcopy(cached[1])
        bars={s:[] for s in symbols}; token=None; seen=set()
        for _ in range(1000):
            params={'symbols':','.join(symbols),'start':start.isoformat(),'end':end.isoformat(),
                    'timeframe':'1Day','adjustment':adjustment,'feed':self.feed,'sort':'asc','limit':10000,
                    'currency':'USD','asof':end.date().isoformat()}
            if token: params['page_token']=token
            payload=self._get('/v2/stocks/bars',params)
            page=payload.get('bars')
            if not isinstance(page,dict): raise DataError('Historical response has no bars mapping.')
            for symbol,rows in page.items():
                if symbol not in bars or not isinstance(rows,list): raise DataError('Unexpected symbols or invalid bars.')
                bars[symbol].extend(rows)
            token=payload.get('next_page_token')
            if not token: break
            if not isinstance(token,str) or token in seen: raise DataError('Invalid or repeated pagination token.')
            seen.add(token)
        else: raise DataError('Pagination exceeded the bounded page limit.')
        # Compare complete snapshots so revisions outside the recent overlap cannot
        # silently survive. This audits incremental changes without claiming lower
        # network volume or a provider guarantee of historical immutability.
        changes=snapshot_changes(cached[1].bars if cached else {},bars)
        result=History(symbols,bars,self.feed,adjustment,datetime.fromtimestamp(self._clock(),timezone.utc).isoformat(),changes)
        self._cache[key]=(self._clock(),result)
        while len(self._cache)>32: self._cache.popitem(last=False)
        # Re-fetch the entire adjusted window on expiry. Incremental splicing is
        # intentionally deferred until revision/corporate-action checks are verified.
        return deepcopy(result)

    def latest_prices(self,symbols,now=None):
        symbols=symbols_checked(symbols); now=utc(now or datetime.now(timezone.utc))
        payload=self._get('/v2/stocks/trades/latest',{'symbols':','.join(symbols),'feed':self.feed})
        trades=payload.get('trades')
        if not isinstance(trades,dict): raise DataError('Latest-trade response has no trades mapping.')
        calendar=xcals.get_calendar('XNYS')
        schedule=calendar.schedule.loc[(now-pd.Timedelta(days=10)).date().isoformat():now.date().isoformat()]
        completed=schedule.loc[schedule['close']<=now]
        if completed.empty: raise DataError('No recent completed exchange session.')
        # In-session: at most 15 minutes old. Closed: close of last completed session,
        # allowing 15 minutes for the final eligible observation on sparse IEX feeds.
        opened=schedule[(schedule['open']<=now)&(schedule['close']>now)]
        threshold=(now if not opened.empty else completed.iloc[-1]['close'])-pd.Timedelta(minutes=15)
        result={}
        for symbol in symbols:
            row=trades.get(symbol,{})
            try: price=float(row['p']); event=utc(row['t'])
            except (KeyError,TypeError,ValueError): raise DataError(f'No valid recent price for {symbol}.') from None
            if not np.isfinite(price) or price<=0 or event>now+pd.Timedelta(seconds=30):
                raise DataError(f'Invalid price or future timestamp for {symbol}.')
            result[symbol]={'price':price,'event_time':event.isoformat(),'retrieved_at':now.isoformat(),
                            'feed':self.feed,'stale':bool(event<threshold),'age_seconds':float((now-event).total_seconds())}
        return result


def prepare_history(history,start,end,asof=None,min_observations=20):
    """Compute adjacent-session returns before dropping incomplete rows."""
    symbols=symbols_checked(history.symbols)
    now=utc(asof or datetime.now(timezone.utc))
    start=utc(start); end=utc(end)
    if start>=end or min_observations<2: raise DataError('Invalid date interval or sample threshold.')
    schedule=xcals.get_calendar('XNYS').schedule.loc[start.date().isoformat():end.date().isoformat()]
    schedule=schedule[(schedule['close']+pd.Timedelta(minutes=15)<=now)&(schedule['close']<=end)]
    sessions=pd.DatetimeIndex(schedule.index).tz_localize(None)
    if len(sessions)<2: raise DataError('No sufficient completed sessions.')
    columns={}
    for symbol in symbols:
        rows=history.bars.get(symbol,[]); observations={}
        if not isinstance(rows,list): raise DataError(f'Malformed daily bars for {symbol}.')
        for row in rows:
            if not isinstance(row,dict): raise DataError(f'Malformed daily bar for {symbol}.')
            try: timestamp=utc(row['t']); price=float(row['c'])
            except (KeyError,TypeError,ValueError): raise DataError(f'Malformed daily bar for {symbol}.') from None
            if not np.isfinite(price) or price<=0: raise DataError(f'Nonpositive or nonfinite price for {symbol}.')
            day=timestamp.tz_convert('America/New_York').normalize().tz_localize(None)
            if day in observations: raise DataError(f'Duplicate daily bar for {symbol}.')
            observations[day]=price
        columns[symbol]=pd.Series(observations,dtype=float).reindex(sessions)
    prices=pd.DataFrame(columns,index=sessions)
    if prices.iloc[-1].isna().any(): raise DataError('Historical data is stale: latest completed session is missing.')
    returns=prices/prices.shift(1)-1
    returns=returns.iloc[1:]
    mask=np.isfinite(returns.to_numpy()).all(axis=1)
    dropped=tuple(str(x.date()) for x in returns.index[~mask]); returns=returns.loc[mask]
    if len(returns)<min_observations: raise DataError(f'Insufficient common daily returns: {len(returns)}; need {min_observations}.')
    identity=hashlib.sha256(returns.to_csv(float_format='%.17g').encode()).hexdigest()
    return Prepared(returns,len(sessions),dropped,str(sessions[-1].date()),identity,
                    {'provider':'Alpaca','feed':history.feed,'adjustment':history.adjustment,
                     'retrieved_at':history.retrieved_at,'period':'daily','refresh':history.refresh,
                     'requested_start':start.isoformat(),'requested_end':end.isoformat(),
                     'analysis_asof':now.isoformat(),'dividend_convention':'provider-adjusted; economic validation pending'})
