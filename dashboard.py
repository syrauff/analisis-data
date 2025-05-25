import pandas as pd
import matplotlib.pyplot as plt
from supabase import create_client, Client
import seaborn as sns 
import streamlit as st
from datetime import date
from babel.numbers import format_currency

# Ganti ini dengan kredensial kamu dari Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


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

# Fungsi yang sudah ada
def categorize_time_of_day(df):
    df["time_category"] = df.hr.apply(lambda x: "Tengah malam" if x < 5 else 
                                         ("Pagi" if x < 12 else 
                                         ("Siang" if x < 15 else
                                        "Sore" if x < 18 else 
                                        "Malam" if x < 22 else "Tengah Malam")))
    
    time_category_counts = df.groupby(by="time_category").instant.nunique().sort_values(ascending=False).reset_index()
    time_category_counts.columns = ["time_category", "unique_count"]
    
    return time_category_counts

all_data = []
limit = 1000
offset = 0

while True:
    response = supabase.table("sharing-bike").select("*").limit(limit).offset(offset).execute()
    data_batch = response.data
    if not data_batch:
        break
    all_data.extend(data_batch)
    offset += limit

all_df = pd.DataFrame(all_data)

# Konversi kolom ke tipe data yang sesuai
convert_dict = {
    "yr": int,
    "hr": int,
    "holiday": bool,
    "workingday": bool,
    "temp": float,
    "atemp": float,
    "hum": float,
    "windspeed": float,
    "casual": int,
    "registered": int,
    "cnt": int,
}

for col, dtype in convert_dict.items():
    if col in all_df.columns:
        all_df[col] = all_df[col].astype(dtype)

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

tab1, tab2, tab3, tab4 = st.tabs(["Pertanyaan Bisnis", "Eksplorasi Tambahan", "Kumpulan   Data", "Olah Data"])

with tab1:
    st.header("Pertanyaan Bisnis")
    st.subheader('Pengguna terdaftar vs pengguna biasa per hari')

    col1, col2 = st.columns(2)

    with col1:
        total_registered = registered_per_day_df['registered'].sum()
        st.metric("Total pengguna terdaftar", value=total_registered)

    with col2:
        total_casual = casual_per_day_df['casual'].sum()
        st.metric("Total pengguna biasa", value=total_casual)


    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(registered_per_day_df['dteday'], registered_per_day_df['registered'], label='Registered', color='blue', marker='o')
    ax.plot(casual_per_day_df['dteday'], casual_per_day_df['casual'], label='Casual', color='orange', marker='o')
    ax.set_title("Pengguna biasa dan terdaftar per hari", fontsize=20)
    ax.set_xlabel("Tanggal", fontsize=15)
    ax.set_ylabel("Total Pengguna", fontsize=15)
    plt.xticks(rotation=45)
    ax.legend()
    st.pyplot(fig)
    #####

    # Mapping musim ke rentang bulan
    season_to_month_range = {
        "Semi": "Januari - Maret",
        "Panas": "April - Juni",
        "Gugur": "Juli - September",
        "Dingin": "Oktober - Desember"
    }

    # Ganti label di pie chart dengan range bulan
    labels = users_by_season_df['season'].map(season_to_month_range)

    # Buat pie chart
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.pie(
        users_by_season_df['total_users'],
        labels=labels,
        autopct='%1.1f%%',
        startangle=90,
        colors=sns.color_palette("coolwarm", len(users_by_season_df))
    )
    ax.axis('equal')  
    ax.set_title("Total Pengguna berdasarkan Rentang Bulan", fontsize=20)
    st.pyplot(fig)

    
    st.subheader('Total Pengguna Mingguan')

    col1, col2 = st.columns(2)
    
    with col1:
        total_weekday_users = round(weekday_count_df['total_users'].mean(), 2)
        st.metric("Rata-rata pengguna", value=total_weekday_users)

    with col2:
        most_active_weekday = weekday_count_df.loc[weekday_count_df['total_users'].idxmax(), 'weekday']
        most_active_weekday_count = weekday_count_df['total_users'].max()  # Mengambil jumlah tertinggi
        st.metric("Penggunaan terbanyak", value=f"{most_active_weekday} ({most_active_weekday_count})")

    
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=weekday_count_df['weekday'], y='total_users', data=weekday_count_df, palette='Blues', ax=ax)
    ax.set_title("Total pengguna berdasarkan hari", fontsize=20)
    ax.set_xlabel("Mingguan", fontsize=15)
    ax.set_ylabel("Total Pengguna", fontsize=15)
    st.pyplot(fig)

    
    st.subheader('Total pengguna berdasarkan jam')

    col1, col2 = st.columns(2)

    with col1:
        total_hourly_users = hour_counts_df['total_users'].sum()
        st.metric("Total pengguna", value=total_hourly_users)

    with col2:
        most_active_hour = hour_counts_df.sort_values(by="total_users", ascending=False).iloc[0]['hr']
        st.metric("Jam paling aktif pengguna", value=f"{most_active_hour}:00")

   
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.lineplot(x='hr', y='total_users', data=hour_counts_df, marker='o', color='green', ax=ax)

    ax.set_xticks(range(24)) 
    ax.set_xticklabels(range(24)) 

    ax.set_title("Total Pengguna berdasarkan Jam", fontsize=20)
    ax.set_xlabel("Pukul", fontsize=15)
    ax.set_ylabel("Total pengguna", fontsize=15)
    st.pyplot(fig)

   
    st.subheader('Total pengguna berdasarkan cuaca')

    col1, col2 = st.columns(2)

    with col1:
        total_users_by_weather = weather_counts_df['total_users'].sum()
        st.metric("Total Pengguna berdasarkan Cuaca", value=total_users_by_weather)

    with col2:
        most_favorable_weather = weather_counts_df.sort_values(by="total_users", ascending=False).iloc[0]['weathersit']
        st.metric("Cuaca paling banyak pengguna", value=most_favorable_weather)

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x='weathersit', y='total_users', data=weather_counts_df, palette='cool', ax=ax)
    ax.set_title("Total Pengguna berdasar cuaca", fontsize=20)
    ax.set_xlabel("Situasi cuaca", fontsize=15)
    ax.set_ylabel("Total pengguna", fontsize=15)
    st.pyplot(fig)

with tab2:
    st.header("Optional Explore")

    st.subheader('Hitung Pengguna berdasarkan waktu')
    col1, col2 = st.columns(2)

    with col1:
        total_time_category_users = time_category_counts['unique_count'].sum()
        st.metric("Total Users by Time Category", value=total_time_category_users)

    with col2:
        most_active_time_category = time_category_counts.loc[time_category_counts['unique_count'].idxmax(), 'time_category']
        most_active_time_category_count = time_category_counts['unique_count'].max()  
        st.metric("Most Active Time Category", value=f"{most_active_time_category} ({most_active_time_category_count})")

    colTre, colOne = st.columns([3, 1]) 
    with colTre:
        # Pie chart dengan matplotlib
        fig, ax = plt.subplots(figsize=(4, 2))
        ax.pie(
            time_category_counts['unique_count'],
            labels=time_category_counts['time_category'],
            autopct='%1.1f%%',
            startangle=90,
            # radius=0.85,
            colors=sns.color_palette('pastel')[0:len(time_category_counts)],
            textprops={'fontsize': 8} 
        )
        ax.axis('equal')  # agar pie tidak lonjong

        # Tampilkan di Streamlit
        st.pyplot(fig)

    with colOne:
        st.markdown('<span style="color:blue">🌞 Pagi: 05:00 - 12:00</span>', unsafe_allow_html=True)
        st.markdown('<span style="color:blue">🌞 Siang: 12:00 - 15:00</span>', unsafe_allow_html=True)
        st.markdown('<span style="color:blue">🌞 Sore: 15:00 - 18:00</span>', unsafe_allow_html=True)
        st.markdown('<span style="color:blue">🌙 Malam: 18:00 - 22:00</span>', unsafe_allow_html=True)
        st.markdown('<span style="color:blue">🌙 Tengah Malam: 22:00 - 05:00</span>', unsafe_allow_html=True)

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

with tab4:
    st.title("📋 Pengolahan Data")
    COLUMN_NAMES = [
        "instant", "dteday", "season", "yr", "mnth", "hr", "holiday", "weekday",
        "workingday", "weathersit", "temp", "atemp", "hum", "windspeed",
        "casual", "registered", "cnt", "time_category"
    ]
    # Opsi untuk input yang umum
    SEASONS_MAP_ID_TO_EN = {"Semi": "Spring", "Panas": "Summer", "Gugur": "Fall", "Dingin": "Winter"}
    SEASONS_MAP_EN_TO_ID = {v: k for k, v in SEASONS_MAP_ID_TO_EN.items()} # For displaying existing data

    MONTHS_ID = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
                "Agustus", "September", "Oktober", "November", "Desember"]
    MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July",
                "August", "September", "October", "November", "December"]
    MONTH_MAP_ID_TO_EN = dict(zip(MONTHS_ID, MONTHS_EN))
    MONTH_MAP_EN_TO_ID = dict(zip(MONTHS_EN, MONTHS_ID))

    WEEKDAYS_ID = ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]
    WEEKDAYS_EN = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"] # Assuming 0 is Sunday for Supabase
    WEEKDAY_MAP_ID_TO_EN = dict(zip(WEEKDAYS_ID, WEEKDAYS_EN))
    WEEKDAY_MAP_EN_TO_ID = dict(zip(WEEKDAYS_EN, WEEKDAYS_ID))

    WEATHERSIT_MAP_ID_TO_EN = {
        "Cerah/Sedikit Berawan": "Clear",
        "Berkabut/Berawan": "Mist + Cloudy",
        "Salju Ringan/Hujan Ringan": "Light Snow/Rain",
        "Hujan Lebat/Badai Es": "Heavy Rain/Ice Pallets"
    }
    WEATHERSIT_MAP_EN_TO_ID = {v: k for k, v in WEATHERSIT_MAP_ID_TO_EN.items()}

    TIME_CATEGORIES_ID = ["Pagi", "Siang", "Sore", "Malam"]
    TIME_CATEGORIES_EN = ["Morning", "Afternoon", "Evening", "Night"] # Assuming these map correctly
    TIME_CATEGORY_MAP_ID_TO_EN = dict(zip(TIME_CATEGORIES_ID, TIME_CATEGORIES_EN))
    TIME_CATEGORY_MAP_EN_TO_ID = dict(zip(TIME_CATEGORIES_EN, TIME_CATEGORIES_ID))


    # Dropdown menu utama
    menu = st.selectbox("Pilih Operasi", ["📄 Lihat Data", "➕ Tambah Data", "✏️ Update Data", "❌ Hapus Data"])

    # Fungsi Read
    if menu == "📄 Lihat Data":

        def get_dynamic_column_names():
            try:
                response = supabase.table("sharing-bike").select("*").limit(1).execute()
                if response.data:
                    return list(response.data[0].keys())
                else:
                    st.warning("Tidak bisa mengambil nama kolom secara dinamis karena tabel kosong. Menggunakan daftar kolom default.")
                    # Pastikan daftar default ini sesuai dengan kolom Anda jika tabel bisa kosong
                    return [
                        "instant", "dteday", "season", "yr", "mnth", "hr", "holiday", "weekday",
                        "workingday", "weathersit", "temp", "atemp", "hum", "windspeed",
                        "casual", "registered", "cnt", "time_category"
                    ]
            except Exception as e:
                st.error(f"Error mengambil nama kolom dinamis: {e}")
                # Fallback jika terjadi error, bisa juga return daftar kolom yang di-hardcode
                return ["instant"] # Minimal satu kolom agar tidak error di index

        current_column_options = get_dynamic_column_names()
        if not current_column_options:
            st.error("Gagal memuat opsi kolom untuk pengurutan. Aplikasi tidak bisa melanjutkan.")
            st.stop() # Hentikan jika tidak ada kolom sama sekali

        # ---- PERUBAHAN 1: Modifikasi definisi fungsi get_data ----
        def get_data(order_column=None, ascending=True, search_id=None, valid_columns=None): # Tambahkan valid_columns
            """
            Mengambil data dari tabel 'sharing-bike' dengan opsi urutan dan pencarian.
            """
            if valid_columns is None: # Pengaman jika valid_columns tidak dikirim
                valid_columns = []

            try:
                query = supabase.table("sharing-bike").select("*")

                if search_id is not None and search_id != "":
                    try:
                        search_id_int = int(search_id)
                        query = query.eq("instant", search_id_int)
                    except ValueError:
                        st.warning("Instant (ID) untuk pencarian harus berupa angka.")
                        return []

                # Gunakan parameter 'valid_columns' untuk validasi
                if order_column and order_column in valid_columns:
                    use_desc = not ascending
                    query = query.order(order_column, desc=use_desc)
                elif order_column:
                    st.warning(f"Kolom '{order_column}' tidak valid untuk pengurutan karena tidak ditemukan dalam daftar kolom yang valid.")

                response = query.execute()
                return response.data
            except Exception as e:
                st.error(f"Error mengambil data: {e}") # Pesan error spesifik dari exception
                return []

        # --- Kontrol untuk Pencarian dan Pengurutan ---
        st.markdown("---")
        st.markdown("##### ⚙️ Kontrol Tampilan Data")

        search_instant_str = st.text_input("Cari berdasarkan Instant (ID):", key="search_id_main_page_v3")

        sort_column = st.selectbox(
            "Urutkan berdasarkan kolom:",
            options=current_column_options,
            index=current_column_options.index('instant') if 'instant' in current_column_options else 0,
            key="sort_col_main_page_v3"
        )

        sort_order_selection = st.radio(
            "Pilih urutan:",
            options=["Ascending", "Descending"],
            index=0,
            key="sort_ord_main_page_v3",
            horizontal=True
        )
        st.markdown("---")

        ascending_bool_for_function = True if sort_order_selection == "Ascending" else False

        # ---- PERUBAHAN 2: Saat memanggil get_data, kirimkan current_column_options ----
        data_pendaftar = get_data(
            order_column=sort_column,
            ascending=ascending_bool_for_function,
            search_id=search_instant_str,
            valid_columns=current_column_options # Kirim daftar kolom yang valid
        )

        if data_pendaftar:
            st.dataframe(data_pendaftar, height=600)
            st.info(f"Menampilkan {len(data_pendaftar)} baris.")
        elif search_instant_str and not data_pendaftar: # Jika ada kriteria pencarian tapi hasil kosong
            st.warning(f"Tidak ada data ditemukan untuk Instant (ID): {search_instant_str}")
        elif not data_pendaftar: # Jika tidak ada kriteria pencarian spesifik dan hasil tetap kosong
            st.warning("Tidak ada data untuk ditampilkan.")
        # Pesan "terjadi kesalahan saat mengambil data" akan muncul jika ada exception di get_data

    # Fungsi Create
    elif menu == "➕ Tambah Data":
        st.subheader("➕ Tambah Data Baru")
        with st.form("form_add"):
            dteday = st.date_input("Tanggal", value=date.today())
            season = st.selectbox("Musim", ["Semi", "Panas", "Gugur", "Dingin"])
            yr = st.number_input("Tahun", value=2011)
            mnth = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
            hr = st.slider("Jam", 0, 23)
            holiday = st.selectbox("Libur?", ["True", "False"])
            weekday = st.selectbox("Hari", ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"])
            workingday = st.selectbox("Hari Kerja?", ["True", "False"])
            weathersit = st.selectbox("Cuaca", [
                "Cerah",
                "Cerah Berawan / Kabut Ringan",
                "Hujan Ringan / Salju",
                "Hujan Lebat / Badai Petir"
            ])
            temp = st.number_input("Suhu", value=0.0, format="%.4f")
            atemp = st.number_input("Suhu Terasa", value=0.0, format="%.4f")
            hum = st.number_input("Kelembapan", value=0.0, format="%.2f")
            windspeed = st.number_input("Kecepatan Angin", value=0.0, format="%.4f")
            casual = st.number_input("Pengguna Kasual", value=0)
            registered = st.number_input("Pengguna Terdaftar", value=0)
            cnt = st.number_input("Total Pengguna", value=0)
            time_category = st.selectbox("Kategori Waktu", ["Pagi", "Siang", "Sore", "Malam", "Tengah Malam"])

            submitted = st.form_submit_button("Tambah")
            if submitted:
                response = supabase.table("sharing-bike").insert({
                    "dteday": dteday.isoformat(),
                    "season": season,
                    "yr": yr,
                    "mnth": mnth,
                    "hr": hr,
                    "holiday": holiday == "True",
                    "weekday": weekday,
                    "workingday": workingday == "True",
                    "weathersit": weathersit,
                    "temp": temp,
                    "atemp": atemp,
                    "hum": hum,
                    "windspeed": windspeed,
                    "casual": casual,
                    "registered": registered,
                    "cnt": cnt,
                    "time_category": time_category
                }).execute()
                st.write("Data berhasil ditambahkan:", response)
                st.success("✅ Data berhasil ditambahkan!")

    # Fungsi Delete
    elif menu == "❌ Hapus Data":
        st.subheader("❌ Hapus Data")
        delete_id = st.number_input("Masukkan 'id' yang ingin dihapus", value=0, step=1)
        if st.button("Hapus"):
            supabase.table("sharing-bike").delete().eq("instant", delete_id).execute()
            st.warning("Data telah dihapus!")

    # Fungsi Update
    elif menu == "✏️ Update Data":
        st.subheader("✏️ Update Data")
        with st.form("form_update"):
            update_id = st.number_input("ID (instant) untuk update", value=1, step=1)

            dteday = st.date_input("Tanggal", value=date(2011, 1, 1), key="upd_dteday")
            season = st.selectbox("Musim", ["Semi", "Panas", "Gugur", "Dingin"], key="upd_season")
            yr = st.number_input("Tahun", value=2011, key="upd_yr")
            mnth = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"], key="upd_mnth")
            hr = st.slider("Jam", 0, 23, key="upd_hr")
            holiday = st.selectbox("Libur?", ["True", "False"], key="upd_holiday")
            weekday = st.selectbox("Hari", ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"], key="upd_weekday")
            workingday = st.selectbox("Hari Kerja?", ["True", "False"], key="upd_workingday")
            weathersit = st.selectbox("Cuaca", [
                "Cerah",
                "Cerah Berawan / Kabut Ringan",
                "Hujan Ringan / Salju",
                "Hujan Lebat / Badai Petir"
            ], key="upd_weathersit")
            temp = st.number_input("Suhu", value=0.0, format="%.4f", key="upd_temp")
            atemp = st.number_input("Suhu Terasa", value=0.0, format="%.4f", key="upd_atemp")
            hum = st.number_input("Kelembapan", value=0.0, format="%.2f", key="upd_hum")
            windspeed = st.number_input("Kecepatan Angin", value=0.0, format="%.4f", key="upd_windspeed")
            casual = st.number_input("Pengguna Kasual", value=0, key="upd_casual")
            registered = st.number_input("Pengguna Terdaftar", value=0, key="upd_registered")
            cnt = st.number_input("Total Pengguna", value=0, key="upd_cnt")
            time_category = st.selectbox("Kategori Waktu", ["Pagi", "Siang", "Sore", "Malam", "Tengah Malam"], key="upd_timecat")

            submitted_update = st.form_submit_button("🔄 Update Data")
            if submitted_update:
                response = supabase.table("sharing-bike").update({
                    "dteday": dteday.isoformat(),
                    "season": season,
                    "yr": int(yr),
                    "mnth": mnth,
                    "hr": str(hr),
                    "holiday": holiday == "True",
                    "weekday": weekday,
                    "workingday": workingday == "True",
                    "weathersit": weathersit,
                    "temp": float(temp),
                    "atemp": float(atemp),
                    "hum": float(hum),
                    "windspeed": str(windspeed),
                    "casual": int(casual),
                    "registered": int(registered),
                    "cnt": int(cnt),
                    "time_category": time_category
                }).eq("instant", update_id).execute()

                if response.data:
                    st.success("✅ Data berhasil diperbarui!")
                else:
                    st.error("❌ Gagal memperbarui data. Pastikan ID ada di database.")
