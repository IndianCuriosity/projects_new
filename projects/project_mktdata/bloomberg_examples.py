
############################################################################################################################################################
# To use Bloomberg's BLPAPI, you need a running Bloomberg Terminal or a Server/B-Pipe connection. While you can use high-level wrappers like xbbg 
# for simpler syntax, the core library requires managing sessions and event loops

# Key Components:
    # Session: The main connection point to Bloomberg services. It can be synchronous or asynchronous.
    # Service: Specific data endpoints like //blp/refdata (static/historical) or //blp/mktdata (real-time streaming).
    # Element: The core data structure used by BLPAPI to handle nested request parameters and response fields.
    # Event Loop: Since data arrives in packets, you must iterate through session.nextEvent() until you receive a RESPONSE event type

############################################################################################################################################################
import blpapi

def main():
    # 1. Setup session options (default localhost:8194)
    options = blpapi.SessionOptions()
    options.setServerHost("localhost")
    options.setServerPort(8194)
    session = blpapi.Session(options)

    # 2. Start the session and open the Reference Data Service
    if not session.start():
        print("Failed to start session.")
        return
    if not session.openService("//blp/refdata"):
        print("Failed to open //blp/refdata service.")
        return

    ref_service = session.getService("//blp/refdata")
    request = ref_service.createRequest("ReferenceDataRequest")

    # 3. Add tickers and fields
    request.append("securities", "AAPL US Equity")
    request.append("fields", "LAST_PRICE")

    # 4. Send the request
    session.sendRequest(request)

    # 5. Process responses (Events)
    while True:
        event = session.nextEvent()
        for msg in event:
            if msg.hasElement("securityData"):
                # Drill down into the response schema
                sec_data = msg.getElement("securityData").getValueAsElement(0)
                field_data = sec_data.getElement("fieldData")
                price = field_data.getElementAsFloat("LAST_PRICE")
                print(f"AAPL Price: {price}")

        if event.eventType() == blpapi.Event.RESPONSE:
            break

if __name__ == "__main__":
    main()




############################################################################################################################################################
# pdblp is a high-level Python wrapper built on top of blpapi that simplifies the process by returning data directly as Pandas DataFrames.It eliminates the need for
# manual event loops and session management, making it much better for interactive research

# Key Functions
    # bdh(): Fetches historical data (comparable to the Excel =BDH function).
    # bdp(): Fetches current/reference data (comparable to =BDP).
    # ref(): Returns reference data for multiple securities and fields.
    #     ref_hist(): Sequential reference data requests, useful for fields that change over time (e.g., historical market cap).

# Why use it?
    # No Boilerplate: You don't have to write your own event handler to parse raw Bloomberg messages.
    # Pandas Native: Data is immediately ready for analysis, plotting, or saving to CSV.
    # Synchronous: By default, it blocks until the request is finished, which is much easier for standard scripts

# Important Note on MaintenanceWhile widely used, 
# pdblp is largely maintenance-only. The original author has released a successor called blp, which is designed to be more extensible and 
# handle modern Bloomberg services like BQL (Bloomberg Query Language) better.


############################################################################################################################################################


import pdblp

# 1. Create a connection object
con = pdblp.BCon(debug=False, port=8194, timeout=5000)

# 2. Start the session
con.start()

# 3. Request historical data (bdh)
# Returns a clean DataFrame with Dates as the index
df = con.bdh(['AAPL US Equity', 'IBM US Equity'], 
             'PX_LAST', '20230101', '20231231')

print(df.head())



############################################################################################################################################################
# Both xbbg and blp are excellent, modern alternatives that reduce boilerplate. While pdblp is the classic choice, these newer libraries are more optimized 
# for high-performance research and Bloomberg Query Language (BQL) support.

# 1. xbbg (The "Human-Friendly" Toolkit)xbbg is currently the most popular choice for quants. It mimics Excel syntax (BDP, BDH, BDS) and is optimized with a 
# Rust-powered engine.Key Feature: Built-in local caching via Parquet files. If you request the same data twice, it pulls from your disk instead of using 
# your daily Bloomberg data limit.Best For: Intraday bars (down to 10-second precision) and real-time streaming


############################################################################################################################################################

from xbbg import blp

# Reference Data (BDP)
ref = blp.bdp(tickers='AAPL US Equity', flds=['NAME', 'GICS_SECTOR_NAME'])

# Historical Data (BDH)
# Returns a MultiIndex DataFrame (Ticker, Field)
hist = blp.bdh('SPX Index', ['high', 'low', 'last_price'], '2024-01-01', '2024-01-10') # Narwhals DataFrame
hist = hist.to_pandas()
hist = hist.pivot_table(index=['ticker','date'], columns='field', values='value')


# Bulk Data (BDS)
members = blp.bds('SPX Index', 'INDX_MEMBERS')

