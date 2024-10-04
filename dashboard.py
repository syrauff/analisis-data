import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns 
import streamlit as st
from babel.numbers import format_currency

sns.set(style='dark')

def create_users_by_season_df(df):
    users_by_season_df = df.groupby(by=["season"])['cnt'].sum().reset_index()
    users_by_season_df.rename(columns={"cnt": "total_users"}, inplace=True)
    
    return users_by_season_df

def create_weekday_user_count_df(df):
    weekday_count_df = df.groupby('weekday')[['registered', 'casual', 'cnt']].sum().reset_index()
    weekday_count_df.rename(columns={"cnt": "total_users"}, inplace=True)
    
    return weekday_count_df

def create_hourly_user_count_df(df):
    hour_counts_df = df.groupby(by="hr")['cnt'].sum().reset_index()
    hour_counts_df.rename(columns={"cnt": "total_users"}, inplace=True)
    
    return hour_counts_df

def create_users_by_weather_df(df):
    weather_counts_df = df.groupby(by=["weathersit"])['cnt'].sum().reset_index()
    weather_counts_df.rename(columns={"cnt": "total_users"}, inplace=True)
    
    return weather_counts_df

def create_users_per_day_df(df):
    registered_per_day_df = df.groupby(by="dteday")['registered'].sum().reset_index()
    casual_per_day_df = df.groupby(by="dteday")['casual'].sum().reset_index()
    
    return registered_per_day_df, casual_per_day_df

def calculate_rfm(df):
    rfm_df = df.groupby(by="weekday", as_index=False).agg({ 
        "dteday": "max", 
        "instant": "nunique",  
        "cnt": "sum"  
    })
    
    rfm_df.columns = ["weekday", "max_order_timestamp", "frequency", "monetary"]
    
    
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["dteday"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    return rfm_df

def categorize_time_of_day(df):
    
    df["time_category"] = df.hr.apply(lambda x: "Night" if x < 7 else 
                                         ("Morning" if x < 12 else 
                                         ("Afternoon" if x < 18 else "Evening")))
    
   
    time_category_counts = df.groupby(by="time_category").instant.nunique().sort_values(ascending=False).reset_index()
    time_category_counts.columns = ["time_category", "unique_count"]
    
    return time_category_counts

all_df = pd.read_csv("all_data.csv")


datetime_columns = ["dteday"]
all_df.sort_values(by="dteday", inplace=True)
all_df.reset_index(drop=True, inplace=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])


min_date = all_df["dteday"].min()
max_date = all_df["dteday"].max()

with st.sidebar:
    st.image("image.jpg", caption="Sharing Bike")
    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

 
    main_df = all_df[(all_df["dteday"] >= pd.to_datetime(start_date)) & 
                     (all_df["dteday"] <= pd.to_datetime(end_date))]


users_by_season_df = create_users_by_season_df(main_df)
weekday_count_df = create_weekday_user_count_df(main_df)
hour_counts_df = create_hourly_user_count_df(main_df)
weather_counts_df = create_users_by_weather_df(main_df)
registered_per_day_df, casual_per_day_df = create_users_per_day_df(main_df)
rfm_df = calculate_rfm(main_df)
time_category_counts = categorize_time_of_day(main_df)


st.header('Sharing Bike :bike:')

tab1, tab2, tab3 = st.tabs(["Answer Business Question", "Optional Explore", "Data"])

with tab1:
    st.header("Answer Business Question")
    st.subheader('Registered vs Casual Users Per Day')

    col1, col2 = st.columns(2)

    with col1:
        total_registered = registered_per_day_df['registered'].sum()
        st.metric("Total Registered Users", value=total_registered)

    with col2:
        total_casual = casual_per_day_df['casual'].sum()
        st.metric("Total Casual Users", value=total_casual)


    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(registered_per_day_df['dteday'], registered_per_day_df['registered'], label='Registered', color='blue', marker='o')
    ax.plot(casual_per_day_df['dteday'], casual_per_day_df['casual'], label='Casual', color='orange', marker='o')
    ax.set_title("Registered and Casual Users Per Day", fontsize=20)
    ax.set_xlabel("Date", fontsize=15)
    ax.set_ylabel("Users", fontsize=15)
    plt.xticks(rotation=45)
    ax.legend()
    st.pyplot(fig)
    #####

    st.subheader('Total Users by Season')

    col1, col2 = st.columns(2)

    with col1:
        total_users_by_season = users_by_season_df['total_users'].sum()
        st.metric("Total Users", value=total_users_by_season)

    with col2:
        most_active_season = users_by_season_df.sort_values(by="total_users", ascending=False).iloc[0]['season']
        st.metric("Most Active Season", value=most_active_season)

    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.pie(users_by_season_df['total_users'], labels=users_by_season_df['season'], autopct='%1.1f%%', startangle=90, colors=sns.color_palette("coolwarm", len(users_by_season_df)))
    ax.axis('equal')  
    ax.set_title("Total Users by Season", fontsize=20)

    st.pyplot(fig)

    
    st.subheader('Total Users by Weekday')

    col1, col2 = st.columns(2)

    with col1:
        total_weekday_users = weekday_count_df['total_users'].sum()
        st.metric("Total Weekday Users", value=total_weekday_users)

    with col2:
        most_active_weekday = weekday_count_df.loc[weekday_count_df['total_users'].idxmax(), 'weekday']
        most_active_weekday_count = weekday_count_df['total_users'].max()  # Mengambil jumlah tertinggi
        st.metric("Most Active Weekday", value=f"{most_active_weekday} ({most_active_weekday_count})")

    
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=weekday_count_df['weekday'], y='total_users', data=weekday_count_df, palette='Blues', ax=ax)
    ax.set_title("Total Users by Weekday", fontsize=20)
    ax.set_xlabel("Weekday", fontsize=15)
    ax.set_ylabel("Total Users", fontsize=15)
    st.pyplot(fig)

    
    st.subheader('Total Users by Hour')

    col1, col2 = st.columns(2)

    with col1:
        total_hourly_users = hour_counts_df['total_users'].sum()
        st.metric("Total Hourly Users", value=total_hourly_users)

    with col2:
        most_active_hour = hour_counts_df.sort_values(by="total_users", ascending=False).iloc[0]['hr']
        st.metric("Most Active Hour", value=f"{most_active_hour}:00")

   
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.lineplot(x='hr', y='total_users', data=hour_counts_df, marker='o', color='green', ax=ax)

    ax.set_xticks(range(24)) 
    ax.set_xticklabels(range(24)) 

    ax.set_title("Total Users by Hour", fontsize=20)
    ax.set_xlabel("Hour", fontsize=15)
    ax.set_ylabel("Total Users", fontsize=15)
    st.pyplot(fig)

   
    st.subheader('Total Users by Weather')

    col1, col2 = st.columns(2)

    with col1:
        total_users_by_weather = weather_counts_df['total_users'].sum()
        st.metric("Total Users by Weather", value=total_users_by_weather)

    with col2:
        most_favorable_weather = weather_counts_df.sort_values(by="total_users", ascending=False).iloc[0]['weathersit']
        st.metric("Most Favorable Weather", value=most_favorable_weather)

   
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x='weathersit', y='total_users', data=weather_counts_df, palette='cool', ax=ax)
    ax.set_title("Total Users by Weather", fontsize=20)
    ax.set_xlabel("Weather Situation", fontsize=15)
    ax.set_ylabel("Total Users", fontsize=15)
    st.pyplot(fig)

with tab2:
    st.header("Optional Explore")
    
    st.subheader("Best Performance Based on RFM Parameters")

    col1, col2, col3 = st.columns(3)

    with col1:
        avg_recency = round(rfm_df.recency.mean(), 1)
        st.metric("Average Recency (days)", value=avg_recency)

    with col2:
        avg_frequency = round(rfm_df.frequency.mean(), 2)
        st.metric("Average Frequency", value=avg_frequency)

    with col3:
        avg_monetary = format_currency(rfm_df.monetary.mean(), "AUD", locale='es_CO') 
        st.metric("Average Monetary", value=avg_monetary)


    fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(20, 10))
    colors = ["#90CAF9"] * 5


    sns.barplot(y="recency", x="weekday", data=rfm_df.sort_values(by="recency", ascending=False).head(5), palette=colors, ax=ax[0])
    ax[0].set_ylabel(None)
    ax[0].set_xlabel("Weekday", fontsize=15)
    ax[0].set_title("By Recency (days)", loc="center", fontsize=20)
    ax[0].tick_params(axis='y', labelsize=10)
    ax[0].tick_params(axis='x', labelsize=10)


    sns.barplot(y="frequency", x="weekday", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
    ax[1].set_ylabel(None)
    ax[1].set_xlabel("Weekday", fontsize=15)
    ax[1].set_title("By Frequency", loc="center", fontsize=20)
    ax[1].tick_params(axis='y', labelsize=10)
    ax[1].tick_params(axis='x', labelsize=10)

  
    sns.barplot(y="monetary", x="weekday", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
    ax[2].set_ylabel(None)
    ax[2].set_xlabel("Weekday", fontsize=15)
    ax[2].set_title("By Monetary", loc="center", fontsize=20)
    ax[2].tick_params(axis='y', labelsize=10)
    ax[2].tick_params(axis='x', labelsize=10)

    st.pyplot(fig)

  
    st.subheader('User Count by Time Category')
    col1, col2 = st.columns(2)

    with col1:
        total_time_category_users = time_category_counts['unique_count'].sum()
        st.metric("Total Users by Time Category", value=total_time_category_users)

    with col2:
        most_active_time_category = time_category_counts.loc[time_category_counts['unique_count'].idxmax(), 'time_category']
        most_active_time_category_count = time_category_counts['unique_count'].max()  
        st.metric("Most Active Time Category", value=f"{most_active_time_category} ({most_active_time_category_count})")

    
    fig, ax = plt.subplots(figsize=(6, 4)) 
    sns.barplot(x='time_category', y='unique_count', data=time_category_counts, palette='pastel', ax=ax)

 
    ax.set_title("User Distribution by Time Category", fontsize=16) 
    ax.set_xlabel("Time Category", fontsize=14)  
    ax.set_ylabel("User Count", fontsize=14)  
    ax.tick_params(axis='x', rotation=15)  

   
    st.pyplot(fig)

with tab3:
    st.header("Data")
    st.subheader("Semua data")
    st.dataframe(all_df)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Data pengguna kasual")
        st.dataframe(casual_per_day_df)
        st.subheader("Data jumlah pengguna setiap hari")
        st.dataframe(weekday_count_df)

    with col2:
        st.subheader("Data Pengguna setiap jam")
        st.dataframe(hour_counts_df)
        st.subheader("Data cuaca setiap jam")
        st.dataframe(weather_counts_df)

    with col3:
        st.subheader("Data pengguna terdaftar")
        st.dataframe(registered_per_day_df)
        st.subheader("Data pengguna kasual")
        st.dataframe(users_by_season_df)

    st.text("Sumber data:")
    st.page_link("https://www.kaggle.com/datasets/lakshmi25npathi/bike-sharing-dataset", label="Kaggle: Sharing Bike", icon="📃")
