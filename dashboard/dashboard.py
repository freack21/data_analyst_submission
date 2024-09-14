import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
sns.set_theme(style='dark')




all_df = pd.read_csv("main_data.csv")
all_df.reset_index(inplace=True)

datetime_columns = ["order_purchase_timestamp","order_approved_at","order_delivered_carrier_date","order_delivered_customer_date","order_estimated_delivery_date"]
for column in datetime_columns:
  all_df[column] = pd.to_datetime(all_df[column])


min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()

with st.sidebar:
    st.image("https://innovationsoftheworld.com/wp-content/uploads/2024/01/3f49143da00cfc426e7a27ba908e9c0a-removebg-preview-1-removebg-preview-300x184.png")

    start_date, end_date = st.date_input(
        label='Rentang Waktu',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )


main_df = all_df[(all_df["order_purchase_timestamp"] >= str(start_date)) & 
                (all_df["order_purchase_timestamp"] <= str(end_date))]

st.header('Olist E-Commerce Dashboard :sparkles:')


# Daily Orders
def create_order_summaries_df(df):
    order_summaries_df = df.resample(rule='D', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "price": "sum",
        "freight_value": "sum",
    }).reset_index()
    order_summaries_df["revenue"] = order_summaries_df["price"] + order_summaries_df["price"]
    order_summaries_df.drop(["price", "freight_value"], axis=1, inplace=True)
    order_summaries_df.rename(columns={
        "order_id": "order_count",
    }, inplace=True)
    
    return order_summaries_df

order_summaries_df = create_order_summaries_df(main_df)

st.subheader('Daily Orders')
 
col1, col2 = st.columns(2)
 
with col1:
    total_orders = order_summaries_df.order_count.sum()
    st.metric("Total orders", value=total_orders)

with col2:
    total_revenue = format_currency(order_summaries_df.revenue.sum(), "AUD", locale='es_CO') 
    st.metric("Total Revenue", value=total_revenue)

fig, ax = plt.subplots(figsize=(20, 10))
ax.plot(
    order_summaries_df["order_purchase_timestamp"],
    order_summaries_df["order_count"],
    marker='o', 
    linewidth=2,
    color="#A0BAFF"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=18)

st.pyplot(fig)





# Best & Worst Performing Product
def create_product_summaries_df(df):
    product_summaries_df = all_df.groupby("product_category_name_english").agg({
        "product_id": "count",
    }).reset_index()
    product_summaries_df.columns = ["product_category", "sold"]
    product_summaries_df.product_category = product_summaries_df.product_category.apply(lambda x: " ".join(x.split("_")).title())
    return product_summaries_df

product_summaries_df = create_product_summaries_df(main_df)

st.subheader("Best & Worst Performing Product")

fig, ax = plt.subplots(nrows=2, ncols=1, figsize=(32, 36))
 
colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(x="sold", y="product_category", hue="product_category", legend=False, data=product_summaries_df.sort_values(by="sold", ascending=False).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel("Product Category")
ax[0].set_xlabel("Number of Sales", fontsize=35)
ax[0].set_title("Best Performing Product", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=35)
ax[0].tick_params(axis='x', labelsize=35)

sns.barplot(x="sold", y="product_category", hue="product_category", legend=False, data=product_summaries_df.sort_values(by="sold", ascending=True).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel("Product Category")
ax[1].set_xlabel("Number of Sales", fontsize=35)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Product", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=35)
ax[1].tick_params(axis='x', labelsize=35)
 
st.pyplot(fig)



# Customer Demographics
def vis_data(s, S, title):
    customer_counts_df = all_df.groupby(f"customer_{s}").agg({
        "customer_id": "nunique",
    }).reset_index()
    customer_counts_df.columns = [S, "Customers"]
    customer_counts_df.sort_values(by="Customers", ascending=False, inplace=True)

    top_3_df = customer_counts_df[:3].copy()

    others_df = pd.DataFrame({
        S: ['Others'],
        'Customers': [customer_counts_df[3:]["Customers"].sum()]
    })

    final_df = pd.concat([top_3_df, others_df], ignore_index=True)

    fig, ax = plt.subplots(figsize=(6, 6))
    plt.pie(
        x=final_df["Customers"],
        labels=final_df[S],
        autopct='%1.1f%%',
        wedgeprops = {'width': .75}
    )
    ax.set_title(title)
    st.pyplot(fig)

st.subheader("Customer Demographics")

col1, col2 = st.columns(2)

with col1:
    vis_data("state", "State", "Customers Count by State") 

with col2:
    vis_data("city", "City", "Customers Count by City") 
 



# RMF
def create_rfm_df(df):
    rfm_df = all_df.groupby(by="customer_id").agg({
        "order_purchase_timestamp": "max",
        "order_id": "count",
        "price": "sum",
        "freight_value": "sum",
    }).reset_index()
    rfm_df["revenue"] = rfm_df["price"] + rfm_df["freight_value"]
    rfm_df.drop(["price", "freight_value"], axis=1, inplace=True)
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = all_df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)

    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    
    return rfm_df

rfm_df = create_rfm_df(main_df)

st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)
 
with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)
 
with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)
 
with col3:
    avg_frequency = format_currency(rfm_df.monetary.mean(), "AUD", locale='es_CO') 
    st.metric("Average Monetary", value=avg_frequency)

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(25, 10))
colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]
 
sns.barplot(y="recency", hue="customer_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("customer_id", fontsize=32)
ax[0].set_title("By Recency (days)", loc="center", fontsize=42)
ax[0].tick_params(axis='y', labelsize=32)
ax[0].tick_params(axis='x', labelsize=35)

sns.barplot(y="frequency", hue="customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("customer_id", fontsize=32)
ax[1].set_title("By Frequency", loc="center", fontsize=42)
ax[1].tick_params(axis='y', labelsize=32)
ax[1].tick_params(axis='x', labelsize=35)

sns.barplot(y="monetary", hue="customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel("customer_id", fontsize=32)
ax[2].set_title("By Monetary", loc="center", fontsize=42)
ax[2].tick_params(axis='y', labelsize=32)
ax[2].tick_params(axis='x', labelsize=35)
 
st.pyplot(fig)
 
st.caption('Made by [Fikri Rivandi](https://freack21.github.io) with <3')