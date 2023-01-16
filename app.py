import datetime as dt
import os
import re

import numpy as np
import pandas as pd
import requests

import streamlit as st
from helpers import *

# Page config
st.set_page_config(page_title='Jamstones Post live',
                   page_icon="Jam.Stones.png", initial_sidebar_state='auto')

# Retrieve app state
app_state = st.experimental_get_query_params()
if "my_saved_result" in app_state:
    last_order_num = int(float(app_state["my_saved_result"][0]))
else:
    last_order_num = 1016

# Select shop
shop = st.selectbox("JS or LV or NA", ["JS", "LV", "NA"])
st.write(f"Selected shop is {shop}")

apikey = st.secrets[shop]['apikey']
password = st.secrets[shop]['password']
hostname = st.secrets[shop]['hostname']

# Get Orders
st.header("Shopee Livestream")
start_date = st.date_input(
    'Start Date', value=dt.date.today()-dt.timedelta(days=1))
end_date = st.date_input('End Date')
query = st.button("Get Orders")

if query:
    # with st.spinner(text="In progress..."):
    df = get_all_orders(apikey, password, hostname)
    df.sort_values(by='created_at', ascending=False, inplace=True)
    df[['created_at']] = df[['created_at']].apply(
        lambda _: pd.to_datetime(_, format='%Y-%m-%d', errors='coerce'))
    df['created_at'] = df['created_at'].apply(lambda x: x.date())
    df = df[(df['created_at'] >= start_date)
            & (df['created_at'] <= end_date)]
    df.rename(columns={'note': 'Notes'}, inplace=True)

    # ShopeeID
    df['ShopeeID'] = df.loc[:, 'Notes']
    df.ShopeeID = df.ShopeeID.astype('str').apply(lambda st: st[st.find(
        "Shopee Order ID: ") + 17:st.find("\n", st.find("Shopee Order ID: "))])
    df['ShopeeNotes'] = df.loc[:, 'Notes']

    # ShopeeNotes
    df.ShopeeNotes = df.ShopeeNotes.astype('str').apply(
        lambda x: x if "Shopee Order Note: " in x else np.nan)
    df.ShopeeNotes = df.ShopeeNotes.astype('str').apply(lambda st: st[st.find(
        "Shopee Order Note: ") + 19:st.find("\n", st.find("Shopee Order Note: "))])

    st.balloons()
    st.download_button(
        "Download your csv file",
        df.to_csv().encode('utf-8'),
        "file.csv",
        "text/csv",
        key='download-csv'
    )

# Upmesh
st.header("Upmesh")

starting_order_num = st.number_input(
    label="Starting Order Num", value=last_order_num, step=1)

if starting_order_num:
    st.experimental_set_query_params(my_saved_result=starting_order_num)
    
order_name_prefix = st.text_input("Order name prefit, I.E #NA or #NAIG or #JS etc")

livestream_file = st.file_uploader(label="Upload upmesh file here")

if livestream_file:
    df = pd.read_csv(livestream_file, encoding='latin1')
    df['line_items'] = df.iloc[:, 22:].values.tolist()
    df['line_items'] = df['line_items'].apply(get_line_items)
    for idx, row in df.iterrows():
        delivery_fee = row['Delivery Fee']
        if delivery_fee > 0:
            row['line_items'].append(
                {"title": 'shipping', "name": 'shipping', "quantity": 1, "price": delivery_fee})
    df = df.fillna('')
    st.write(df)
    upload = st.button(label="Upload the following file")

    if upload:
        for index, row in df.iterrows():

            payload = {}

            payload['note'] = "Buyer Name: " + str(row['ï»¿Buyer FB']) + "\n Delivery Method: " + str(
                row['Delivery Method']) + "\n Delivery Instruction: " + str(row['Delivery Instruction'])
            if pd.notna(row['Email']):
                payload['email'] = row['Email']
            payload['name'] = f"{order_name_prefix}{str(index+starting_order_num).zfill(4)}"
            payload["shipping_address"] = {
                "address1": row["Buyer Address"],
                "phone": row["Contact No."],
                "zip": row["Postal Code"],
                "city": "Singapore",
                "name": row["Delivery Name"],
                "country": "Singapore",
                "country_code": "SG",
            }
            payload['line_items'] = row['line_items']
        #     payload["customer"] = {
        #         "email": row['Email'],
        #         "first_name": row["Delivery Name"]
        #     }

            # POST
            url = f"https://{apikey}:{password}@{hostname}/admin/api/2023-01/orders.json"
            order = {"order": payload}
            # print(payload)
            print(url)
            try:
                data = (requests.post(url, json=order))
                print("+++"*30)
                if data.status_code != 201:
                    st.error(
                        f"Error with #IG{shop}{str(index+starting_order_num).zfill(4)} \n code:{data.status_code} \n {data.text}")
                    print(
                        payload['name'] + f" payload success compiled, request invalid \n code:{data.status_code} \n {data.text}")
                    break
                else:
                    st.success(
                        f"Done with #IG{shop}{str(index+starting_order_num).zfill(4)}")
                    print(payload['name'] + " success")
            except Exception as e:
                print(e)
                st.error(
                    f"Error with #IG{shop}{str(index+starting_order_num).zfill(4)} \n {e}")
                st.write(payload)
                print(payload)
                break
        #     print(data.text)
