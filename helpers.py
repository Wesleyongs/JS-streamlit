import pandas as pd
import requests
import datetime as dt


def get_all_orders(apikey, password, hostname):
    last = 0
    orders = pd.DataFrame()
    while True:
        url = f"https://{apikey}:{password}@{hostname}/admin/api/2021-10/orders.json?limit=250&fulfillment_status=unfulfilled&since_id={last}"
        response = requests.request("GET", url)

        df = pd.DataFrame(response.json()['orders'])
        orders = pd.concat([orders, df])
        last = df['id'].iloc[-1]
        if len(df) < 250:
            break
    return (orders)


def get_line_items(row):
    num_items = int(len(row)/5 + 1)
    res_list = []

    for i in range(1, num_items):
        title = row[i*5-5]
        name = row[i*5-4]
        qty = row[i*5-3]
        price = row[i*5-2]
        if pd.notna(title):
            res_list.append({
                "product_id": "4718966800480",
                "title": title,
                "name": name,
                "quantity": int(qty),
                "price": int(price)
            })

    return res_list


def add_discount(df):
    if int(df['Promo Deduction']) > 0:
        df['line_items'].append(
            {
                "product_id": "4718966800480",
                "title": df['Promo Code'],
                "name": df['Promo Code'],
                "quantity": 1,
                "price": -int(df['Promo Deduction'])
            })
    return df
