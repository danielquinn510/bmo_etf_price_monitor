from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

#Load price data
PRICES_DF = pd.read_csv('bankofmontreal-e134q-1arsjzss-prices.csv')
PRICES_DF['DATE'] = pd.to_datetime(PRICES_DF['DATE'])
PRICES_DF.set_index('DATE', inplace=True)

#Data manipulation function
@app.route('/api/analyze', methods=['POST'])
def analyze_etf():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
        
    file = request.files['file']
    weights_df = pd.read_csv(file)
    
    start_date = PRICES_DF.index.min()
    initial_prices = PRICES_DF.loc[start_date]
    shares = {}
    weights_info = []
    
    for _, row in weights_df.iterrows():
        stock = row['name']
        weight = row['weight']
        if stock in PRICES_DF.columns:
            shares[stock] = (1000 * weight) / initial_prices[stock]
            weights_info.append({
                "name": stock,
                "weight": weight
            })

    relevant_prices = PRICES_DF[list(shares.keys())].copy()
    
    #Historical Price Data
    history_df = relevant_prices.copy()
    history_df.index = history_df.index.strftime('%Y-%m-%d')
    history_json = history_df.to_dict(orient='index')

    #Calculate reconstructed ETF prices
    for stock, count in shares.items():
        relevant_prices[stock] *= count
    
    daily_series = relevant_prices.sum(axis=1)
    monthly_series = daily_series.groupby([daily_series.index.year, daily_series.index.month]).tail(1)

    #Helper for formatting chart
    def to_chart_data(series):
        return [{"date": date.strftime('%Y-%m-%d'), "value": round(val, 2)} 
                for date, val in series.items()]

    return jsonify({
        "table": weights_info,
        "daily_chart": to_chart_data(daily_series),
        "monthly_chart": to_chart_data(monthly_series),
        "shares": shares,
        "history": history_json
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)