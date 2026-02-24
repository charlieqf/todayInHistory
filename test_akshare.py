# coding=utf-8
import akshare as ak

stocks = {
    '重庆啤酒 (Xu Xiang)': ('600132', '20111101', '20120228'),
    '中国中车 (Zhao Laoge)': ('601766', '20150301', '20150701'),
    '东方通信 (10x Demon)': ('600776', '20181001', '20190331')
}

print('Testing Akshare Data Retrieval API:\n')
for name, (symbol, start, end) in stocks.items():
    try:
        df = ak.stock_zh_a_hist(symbol=symbol, period='daily', start_date=start, end_date=end, adjust='qfq')
        print(f'✅ {name}: Retrieved {len(df)} days of data ({start} - {end}).')
        if len(df) > 0:
            print(f"   Columns: {list(df.columns)[:5]}")
            print(f"   First row sample:\n{df.head(1).to_string(index=False)}")
            
    except Exception as e:
        print(f'❌ {name}: Failed to retrieve data - {e}')
