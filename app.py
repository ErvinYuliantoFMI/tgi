"""
TGI WMS - Warehouse Management System sederhana
Data source: file CSV (data/customers.csv, data/products.csv,
             data/orders.csv, data/order_items.csv)

Cara menjalankan:
    pip install -r requirements.txt
    streamlit run app.py
"""

import base64
import os
import uuid
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_option_menu import option_menu

# ---------------------------------------------------------------------------
# Konfigurasi & path data
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

CUSTOMERS_CSV = os.path.join(DATA_DIR, "customers.csv")
PRODUCTS_CSV = os.path.join(DATA_DIR, "products.csv")
ORDERS_CSV = os.path.join(DATA_DIR, "orders.csv")
ORDER_ITEMS_CSV = os.path.join(DATA_DIR, "order_items.csv")

STATUSES = ["Pesanan Masuk", "Diproses", "Dikirim", "Selesai"]

STATUS_COLOR = {
    "Pesanan Masuk": "#B7791F",
    "Diproses": "#2C5F8A",
    "Dikirim": "#FBAF43",
    "Selesai": "#3F6B33",
}

# Brand colors (diambil dari Logo-TGI.png)
NAVY = "#1E2442"
AMBER = "#FBAF43"
NAVY_SOFT = "#2A3357"
CREAM = "#F7F5F1"

LOGO_PATH = os.path.join(BASE_DIR, "assets", "logo-tgi.png")
LOGO_WHITE_PATH = os.path.join(BASE_DIR, "assets", "logo-tgi-putih.png")
ICON_PATH = os.path.join(BASE_DIR, "assets", "logo-icon.png")

COMPANY = {
    "name": "PT Tanaka Graha Indonesia",
    "location": "Jakarta – Indonesia",
    "address": "Jl. Meruya Ilir Raya No.3, Meruya Utara, Kec. Kembangan, "
                "Kota Jakarta Barat, Daerah Khusus Ibukota Jakarta 11630",
    "email": "tanakagraha.id@gmail.com",
    "instagram": "https://www.instagram.com/tanakagraha/",
}

STATS = [
    ("4 Tahun", "Pengalaman menghadirkan kebahagiaan bagi pelanggan."),
    ("100%", "Dedikasi menyediakan solusi terbaik untuk setiap kebutuhan pelanggan."),
    ("200+", "Klien yang puas dan senang bekerja sama dengan kami."),
]

WHY_US = [
    ("🏆", "Best Brand", "Sebagai distributor daging sapi dan seafood di Indonesia, kami selalu menjaga kualitas produk demi kepuasan pelanggan."),
    ("☑️", "Halal Certified", "Mulai dari proses penyembelihan, penyimpanan, pemotongan, hingga pengemasan — seluruhnya dijamin halal."),
    ("⚡", "Quick Process", "Pesanan diproses dengan cepat sesuai preferensi dan kebutuhan pelanggan."),
    ("💎", "Premium Quality", "Semua produk dijamin sesuai label dari supplier kami, terutama untuk daging impor."),
    ("🏷️", "Affordable Price", "Harga mulai dari Rp 40.000 tanpa minimum order."),
    ("💡", "Innovative", "Terus berinovasi memperkenalkan produk dan varian baru melalui riset dan pengembangan."),
]

SERVICES = [
    ("🏬", "Online & Offline Store", "Terinspirasi dari Australia Meat Emporium, menghadirkan konsep toko daging dengan gaya yang segar dan modern."),
    ("❄️", "Storage", "Menjaga kondisi cold storage terbaik pada suhu standar -18°C hingga -20°C sebagai importir dan distributor."),
    ("🚛", "Transportation", "Pengiriman dari gudang ke mitra outlet menggunakan reefer truck dengan kontrol suhu standar untuk menjaga kualitas produk."),
]

st.set_page_config(page_title="TGI WMS", page_icon="📦", layout="wide")

st.markdown(
    f"""
    <style>
    [data-testid="stSidebar"] {{
        background-color: {NAVY};
    }}
    [data-testid="stSidebar"] * {{
        color: #EDE9DF;
    }}
    [data-testid="stSidebar"] hr {{
        border-color: {NAVY_SOFT};
    }}
    [data-testid="stSidebar"] [data-baseweb="radio"] label {{
        color: #EDE9DF !important;
    }}
    [data-testid="stSidebar"] iframe {{
        background-color: {NAVY} !important;
    }}
    div.stButton > button[kind="primary"] {{
        background-color: {AMBER};
        border-color: {AMBER};
        color: {NAVY};
        font-weight: 600;
    }}
    div.stButton > button[kind="primary"]:hover {{
        background-color: #E89B2B;
        border-color: #E89B2B;
        color: {NAVY};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Helper baca / tulis CSV
# ---------------------------------------------------------------------------

def load_customers() -> pd.DataFrame:
    return pd.read_csv(CUSTOMERS_CSV, dtype={"customer_id": str})


def load_products() -> pd.DataFrame:
    df = pd.read_csv(PRODUCTS_CSV, dtype={"product_id": str})
    df["stock"] = df["stock"].astype(int)
    df["price"] = df["price"].astype(float)
    return df


def save_products(df: pd.DataFrame):
    df.to_csv(PRODUCTS_CSV, index=False)


def load_orders() -> pd.DataFrame:
    df = pd.read_csv(ORDERS_CSV, dtype={"order_id": str, "customer_id": str})
    return df


def save_orders(df: pd.DataFrame):
    df.to_csv(ORDERS_CSV, index=False)


def load_order_items() -> pd.DataFrame:
    df = pd.read_csv(
        ORDER_ITEMS_CSV, dtype={"order_id": str, "product_id": str}
    )
    df["qty"] = df["qty"].astype(int)
    return df


def save_order_items(df: pd.DataFrame):
    df.to_csv(ORDER_ITEMS_CSV, index=False)


def rupiah(n) -> str:
    return "Rp " + f"{n:,.0f}".replace(",", ".")


def next_order_id(orders: pd.DataFrame) -> str:
    if orders.empty:
        return "SO-24095"
    nums = (
        orders["order_id"]
        .str.replace("SO-", "", regex=False)
        .astype(int)
    )
    return f"SO-{nums.max() + 1}"


def next_product_id(products: pd.DataFrame) -> str:
    if products.empty:
        return "P1"
    nums = products["product_id"].str.replace("P", "", regex=False).astype(int)
    return f"P{nums.max() + 1}"


# ---------------------------------------------------------------------------
# Sidebar navigasi
# ---------------------------------------------------------------------------

if os.path.exists(LOGO_WHITE_PATH):
    st.sidebar.image(LOGO_WHITE_PATH, use_container_width=True)
elif os.path.exists(LOGO_PATH):
    st.sidebar.image(LOGO_PATH, use_container_width=True)
else:
    st.sidebar.markdown("### TGI Warehouse")
st.sidebar.markdown(
    "<div style='letter-spacing:1px;font-size:11px;color:#FFFFFF;"
    "text-transform:uppercase;margin-top:-6px;'>Warehouse Management System</div>",
    unsafe_allow_html=True,
)
st.sidebar.write("")

MENU_OPTIONS = ["Profil Perusahaan", "Dashboard", "Input Pesanan", "Daftar Pesanan", "Master Barang"]
MENU_ICONS = ["building", "speedometer2", "cart-plus-fill", "list-check", "boxes"]

with st.sidebar:
    page = option_menu(
        menu_title=None,
        options=MENU_OPTIONS,
        icons=MENU_ICONS,
        default_index=0,
        styles={
            "container": {
                "padding": "0",
                "background-color": NAVY,
            },
            "icon": {"color": "#8D95A6", "font-size": "15px"},
            "nav-link": {
                "font-size": "14.5px",
                "text-align": "left",
                "margin": "3px 0",
                "padding": "10px 14px",
                "color": "#C7CCDA",
                "background-color": "transparent",
                "border-radius": "6px",
            },
            "nav-link:hover": {
                "background-color": "rgba(255,255,255,0.06)",
                "color": "#FFFFFF",
            },
            "nav-link-selected": {
                "background-color": "rgba(251,175,67,0.14)",
                "color": "#FFFFFF",
                "icon-color": AMBER,
                "font-weight": "600",
                "border-left": f"3px solid {AMBER}",
                "border-radius": "6px",
            },
        },
    )

# ---------------------------------------------------------------------------
# Halaman: Dashboard
# ---------------------------------------------------------------------------

CHART_LAYOUT = dict(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(family="Arial, sans-serif", color="#1C2B33", size=12),
    margin=dict(l=10, r=10, t=30, b=10),
    height=320,
)


def page_dashboard():
    st.title("Dashboard")
    st.caption("Ringkasan pesanan dan stock gudang")

    orders = load_orders()
    products = load_products()
    customers = load_customers()
    order_items = load_order_items()

    total_pesanan = len(orders)
    stock_tersedia = int(products["stock"].sum())

    # --- KPI cards dengan background -----------------------------------------
    stock_display = f"{stock_tersedia:,}".replace(",", ".")

    st.markdown(_html(f"""
    <style>
    .tgi-kpi-wrap {{
        display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px;
        margin-bottom: 8px;
    }}
    .tgi-kpi {{
        border-radius: 10px; padding: 24px 28px; position: relative;
        overflow: hidden; box-shadow: 0 6px 18px rgba(30,36,66,0.12);
    }}
    .tgi-kpi .glyph {{
        position: absolute; right: 14px; top: 8px; font-size: 56px; opacity: 0.18;
    }}
    .tgi-kpi .label {{
        font-size: 12.5px; font-weight: 600; letter-spacing: 1px;
        text-transform: uppercase; position: relative; z-index: 1;
    }}
    .tgi-kpi .value {{
        font-size: 38px; font-weight: 800; font-family: monospace;
        margin-top: 8px; position: relative; z-index: 1;
    }}
    .tgi-kpi-navy {{
        background: linear-gradient(135deg, {NAVY} 0%, {NAVY_SOFT} 100%);
        color: #FFFFFF;
    }}
    .tgi-kpi-navy .label {{ color: #C7CCDA; }}
    .tgi-kpi-amber {{
        background: linear-gradient(135deg, {AMBER} 0%, #E2891F 100%);
        color: {NAVY};
    }}
    .tgi-kpi-amber .label {{ color: #5A3E10; }}
    @media (max-width: 700px) {{
        .tgi-kpi-wrap {{ grid-template-columns: 1fr; }}
    }}
    </style>
    <div class="tgi-kpi-wrap">
        <div class="tgi-kpi tgi-kpi-navy">
            <div class="glyph">🧾</div>
            <div class="label">Total Pesanan</div>
            <div class="value">{total_pesanan}</div>
        </div>
        <div class="tgi-kpi tgi-kpi-amber">
            <div class="glyph">📦</div>
            <div class="label">Stock Tersedia</div>
            <div class="value">{stock_display} unit</div>
        </div>
    </div>
    """),
        unsafe_allow_html=True,
    )

    st.write("")
    row1_left, row1_right = st.columns(2)

    # --- Grafik: Pesanan per Status (donut) ---------------------------------
    with row1_left:
        st.subheader("Pesanan per Status")
        if orders.empty:
            st.info("Belum ada pesanan.")
        else:
            status_counts = (
                orders["status"].value_counts().reindex(STATUSES, fill_value=0)
                .reset_index()
            )
            status_counts.columns = ["status", "jumlah"]
            fig = px.pie(
                status_counts, names="status", values="jumlah", hole=0.6,
                color="status", color_discrete_map=STATUS_COLOR,
            )
            fig.update_traces(
                textposition="outside", textinfo="label+value",
                marker=dict(line=dict(color="#FFFFFF", width=2)),
            )
            fig.update_layout(
                **{**CHART_LAYOUT, "margin": dict(l=10, r=10, t=30, b=10)},
                showlegend=False,
                annotations=[dict(
                    text=f"<b>{total_pesanan}</b><br>Pesanan", x=0.5, y=0.5,
                    font=dict(size=16, color=NAVY), showarrow=False,
                )],
            )
            st.plotly_chart(fig, use_container_width=True)

    # --- Grafik: Trend Pesanan Harian (area halus) --------------------------
    with row1_right:
        st.subheader("Trend Pesanan Harian")
        if orders.empty:
            st.info("Belum ada pesanan.")
        else:
            trend = orders.groupby("order_date").size().reset_index(name="jumlah")
            trend["order_date"] = pd.to_datetime(trend["order_date"])
            trend = trend.sort_values("order_date")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=trend["order_date"], y=trend["jumlah"],
                mode="lines+markers", line=dict(color="#2C5F8A", width=3, shape="spline"),
                marker=dict(size=9, color="#2C5F8A", line=dict(color="#FFFFFF", width=1.5)),
                fill="tozeroy", fillcolor="rgba(44,95,138,0.15)",
            ))
            fig.update_layout(
                **CHART_LAYOUT, xaxis_title=None, yaxis_title="Jumlah Pesanan",
            )
            st.plotly_chart(fig, use_container_width=True)

    row2_left, row2_right = st.columns(2)

    # --- Grafik: Stock per Barang (lollipop) --------------------------------
    with row2_left:
        st.subheader("Stock per Barang")
        if products.empty:
            st.info("Belum ada data barang.")
        else:
            stock_df = products[["name", "stock"]].sort_values("stock")
            colors = ["#A3402E" if s < 200 else "#1F6F5C" for s in stock_df["stock"]]
            fig = go.Figure()
            for _, row in stock_df.iterrows():
                color = "#A3402E" if row["stock"] < 200 else "#1F6F5C"
                fig.add_shape(
                    type="line", x0=0, x1=row["stock"], y0=row["name"], y1=row["name"],
                    line=dict(color=color, width=3),
                )
            fig.add_trace(go.Scatter(
                x=stock_df["stock"], y=stock_df["name"], mode="markers+text",
                marker=dict(size=16, color=colors, line=dict(color="#FFFFFF", width=1.5)),
                text=stock_df["stock"], textposition="middle right",
                textfont=dict(size=11, color="#1C2B33"),
            ))
            fig.update_layout(
                **CHART_LAYOUT, xaxis_title="Stock", yaxis_title=None, showlegend=False,
            )
            fig.update_xaxes(range=[0, stock_df["stock"].max() * 1.25])
            st.plotly_chart(fig, use_container_width=True)

    # --- Grafik: Item Terlaris (bar gradient bulat) -------------------------
    with row2_right:
        st.subheader("Item Terlaris (berdasarkan Qty Dipesan)")
        if order_items.empty:
            st.info("Belum ada item pesanan.")
        else:
            item_qty = (
                order_items.groupby("product_id")["qty"].sum().reset_index()
                .merge(products[["product_id", "name"]], on="product_id", how="left")
                .sort_values("qty", ascending=True).tail(5)
            )
            amber_shades = ["#FDE3B8", "#FBCB80", "#FBAF43", "#E2891F", "#B96B15"]
            n = len(item_qty)
            shades = amber_shades[-n:] if n <= len(amber_shades) else amber_shades * n
            fig = go.Figure(go.Bar(
                x=item_qty["qty"], y=item_qty["name"], orientation="h",
                marker=dict(color=shades[:n], cornerradius=8,
                            line=dict(color="#FFFFFF", width=1)),
                text=item_qty["qty"], textposition="outside",
            ))
            fig.update_layout(
                **CHART_LAYOUT, xaxis_title="Total Qty Dipesan", yaxis_title=None,
            )
            st.plotly_chart(fig, use_container_width=True)

    st.write("")
    st.subheader("Pesanan Terbaru")
    if orders.empty:
        st.info("Belum ada pesanan.")
    else:
        recent = orders.merge(
            customers[["customer_id", "name"]], on="customer_id", how="left"
        ).sort_values("order_date", ascending=False).head(5)
        show = recent[["order_id", "name", "order_date", "status"]].rename(
            columns={"order_id": "No. Pesanan", "name": "Customer",
                     "order_date": "Tanggal", "status": "Status"}
        )
        st.dataframe(show, hide_index=True, use_container_width=True)


# ---------------------------------------------------------------------------
# Halaman: Input Pesanan
# ---------------------------------------------------------------------------

def page_input_pesanan():
    st.title("Input Pesanan")
    st.caption("Buat pesanan penjualan baru")

    customers = load_customers()
    products = load_products()

    if "order_items" not in st.session_state:
        st.session_state.order_items = [{"key": str(uuid.uuid4()), "product_id": "", "qty": 1}]

    def add_item_row():
        st.session_state.order_items.append(
            {"key": str(uuid.uuid4()), "product_id": "", "qty": 1}
        )

    def remove_item_row(key):
        st.session_state.order_items = [
            it for it in st.session_state.order_items if it["key"] != key
        ]
        if not st.session_state.order_items:
            st.session_state.order_items = [
                {"key": str(uuid.uuid4()), "product_id": "", "qty": 1}
            ]

    cust_options = ["-- Pilih customer --"] + customers["name"].tolist()
    cust_choice = st.selectbox("Customer", cust_options)

    default_address = ""
    customer_id = None
    if cust_choice != "-- Pilih customer --":
        row = customers[customers["name"] == cust_choice].iloc[0]
        customer_id = row["customer_id"]
        default_address = row["address"]

    col1, col2 = st.columns(2)
    with col1:
        order_date = st.date_input("Tanggal Pesanan", value=date.today())
    with col2:
        st.write("")

    address = st.text_area("Alamat Kirim", value=default_address, height=70)

    st.markdown("**Detail Item Pesanan**")

    total = 0
    for item in st.session_state.order_items:
        c1, c2, c3, c4 = st.columns([3, 1.2, 1.5, 0.6])
        with c1:
            options = ["-- Pilih item --"] + [
                f"{r['name']} — stok {r['stock']} {r['unit']}"
                for _, r in products.iterrows()
            ]
            product_ids = [None] + products["product_id"].tolist()
            current_idx = 0
            if item["product_id"]:
                try:
                    current_idx = product_ids.index(item["product_id"])
                except ValueError:
                    current_idx = 0
            selected = st.selectbox(
                "Item", options, index=current_idx, key=f"prod_{item['key']}",
                label_visibility="collapsed",
            )
            if selected != "-- Pilih item --":
                item["product_id"] = product_ids[options.index(selected)]
            else:
                item["product_id"] = ""
        with c2:
            item["qty"] = st.number_input(
                "Qty", min_value=1, value=int(item["qty"]), step=1,
                key=f"qty_{item['key']}", label_visibility="collapsed",
            )
        with c3:
            if item["product_id"]:
                prow = products[products["product_id"] == item["product_id"]].iloc[0]
                subtotal = prow["price"] * item["qty"]
                total += subtotal
                st.markdown(f"<div style='padding-top:8px;font-family:monospace;'>{rupiah(subtotal)}</div>",
                            unsafe_allow_html=True)
            else:
                st.markdown("<div style='padding-top:8px;color:#9C9585;'>—</div>", unsafe_allow_html=True)
        with c4:
            st.button("🗑", key=f"remove_{item['key']}",
                       on_click=remove_item_row, args=(item["key"],))

    st.button("+ Tambah Item", on_click=add_item_row)

    st.divider()
    st.markdown(f"### Total Pesanan: {rupiah(total)}")

    if st.button("Simpan Pesanan", type="primary"):
        errors = []
        if customer_id is None:
            errors.append("Pilih customer.")
        if not address.strip():
            errors.append("Alamat kirim wajib diisi.")
        valid_items = [it for it in st.session_state.order_items if it["product_id"] and it["qty"] > 0]
        if not valid_items:
            errors.append("Tambahkan minimal satu item pesanan.")
        for it in valid_items:
            prow = products[products["product_id"] == it["product_id"]].iloc[0]
            if it["qty"] > prow["stock"]:
                errors.append(f"Qty \"{prow['name']}\" melebihi stock tersedia ({prow['stock']}).")

        if errors:
            for e in errors:
                st.error(e)
        else:
            orders = load_orders()
            order_items = load_order_items()

            new_id = next_order_id(orders)
            new_order = pd.DataFrame([{
                "order_id": new_id,
                "customer_id": customer_id,
                "order_date": order_date.isoformat(),
                "address": address.strip(),
                "status": "Pesanan Masuk",
            }])
            orders = pd.concat([orders, new_order], ignore_index=True)
            save_orders(orders)

            new_items = pd.DataFrame([{
                "order_id": new_id,
                "product_id": it["product_id"],
                "qty": it["qty"],
            } for it in valid_items])
            order_items = pd.concat([order_items, new_items], ignore_index=True)
            save_order_items(order_items)

            st.session_state.order_items = [{"key": str(uuid.uuid4()), "product_id": "", "qty": 1}]
            st.success(f"Pesanan {new_id} berhasil disimpan.")
            st.rerun()


# ---------------------------------------------------------------------------
# Halaman: Daftar Pesanan
# ---------------------------------------------------------------------------

def page_daftar_pesanan():
    st.title("Daftar Pesanan")
    st.caption("Semua pesanan dan status prosesnya")

    orders = load_orders()
    order_items = load_order_items()
    products = load_products()
    customers = load_customers()

    col1, col2 = st.columns([2, 1])
    with col1:
        query = st.text_input("Cari no. pesanan atau customer", "")
    with col2:
        status_filter = st.selectbox("Status", ["Semua"] + STATUSES)

    merged = orders.merge(
        customers[["customer_id", "name"]], on="customer_id", how="left"
    )

    if query:
        q = query.lower()
        merged = merged[
            merged["order_id"].str.lower().str.contains(q)
            | merged["name"].str.lower().str.contains(q)
        ]
    if status_filter != "Semua":
        merged = merged[merged["status"] == status_filter]

    if merged.empty:
        st.info("Tidak ada pesanan yang cocok.")
        return

    for _, o in merged.sort_values("order_date", ascending=False).iterrows():
        items = order_items[order_items["order_id"] == o["order_id"]].merge(
            products, on="product_id", how="left"
        )
        items_total = (items["qty"] * items["price"]).sum() if not items.empty else 0

        with st.expander(f"{o['order_id']} — {o['name']} — {rupiah(items_total)}"):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"**Tanggal Pesanan:** {o['order_date']}")
                st.write(f"**Alamat Kirim:** {o['address']}")
                if not items.empty:
                    show = items[["name", "qty", "unit", "price"]].copy()
                    show["subtotal"] = show["qty"] * show["price"]
                    show["price"] = show["price"].apply(rupiah)
                    show["subtotal"] = show["subtotal"].apply(rupiah)
                    show = show.rename(columns={
                        "name": "Item", "qty": "Qty", "unit": "Satuan",
                        "price": "Harga", "subtotal": "Subtotal",
                    })
                    st.dataframe(show, hide_index=True, use_container_width=True)
            with c2:
                new_status = st.selectbox(
                    "Status Pesanan", STATUSES,
                    index=STATUSES.index(o["status"]),
                    key=f"status_{o['order_id']}",
                )
                if new_status != o["status"]:
                    orders.loc[orders["order_id"] == o["order_id"], "status"] = new_status
                    save_orders(orders)
                    st.success(f"Status {o['order_id']} diubah menjadi \"{new_status}\"")
                    st.rerun()


# ---------------------------------------------------------------------------
# Halaman: Master Barang
# ---------------------------------------------------------------------------

def page_master_barang():
    st.title("Master Barang")
    st.caption("Kelola data barang dan stock")

    products = load_products()

    with st.form("form_tambah_barang", clear_on_submit=True):
        st.markdown("**Tambah Barang Baru**")
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Nama Barang", placeholder="mis. Kardus Box Sedang")
            stock = st.number_input("Stock Awal", min_value=0, value=0, step=1)
        with c2:
            unit = st.text_input("Satuan", placeholder="mis. pcs, roll, unit")
            price = st.number_input("Harga Satuan", min_value=0, value=0, step=500)
        submitted = st.form_submit_button("Simpan Barang", type="primary")

        if submitted:
            if not name.strip() or not unit.strip():
                st.error("Nama barang dan satuan wajib diisi.")
            else:
                new_id = next_product_id(products)
                new_row = pd.DataFrame([{
                    "product_id": new_id, "name": name.strip(), "unit": unit.strip(),
                    "stock": int(stock), "price": float(price),
                }])
                products = pd.concat([products, new_row], ignore_index=True)
                save_products(products)
                st.success(f'Barang "{name}" ditambahkan.')
                st.rerun()

    st.divider()
    st.markdown(f"**Daftar Barang ({len(products)})** — ubah stock/harga langsung di tabel lalu klik Simpan Perubahan")

    edited = st.data_editor(
        products,
        column_config={
            "product_id": st.column_config.TextColumn("Kode", disabled=True),
            "name": st.column_config.TextColumn("Nama Barang", disabled=True),
            "unit": st.column_config.TextColumn("Satuan", disabled=True),
            "stock": st.column_config.NumberColumn("Stock", min_value=0, step=1),
            "price": st.column_config.NumberColumn("Harga", min_value=0, step=500, format="Rp %d"),
        },
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        key="products_editor",
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Simpan Perubahan", type="primary"):
            save_products(edited)
            st.success("Data barang diperbarui.")
            st.rerun()
    with col2:
        del_options = ["-- Pilih barang untuk dihapus --"] + [
            f"{r['product_id']} — {r['name']}" for _, r in products.iterrows()
        ]
        to_delete = st.selectbox("Hapus barang", del_options, label_visibility="collapsed")
        if to_delete != "-- Pilih barang untuk dihapus --":
            if st.button("Hapus", type="secondary"):
                pid = to_delete.split(" — ")[0]
                products = products[products["product_id"] != pid]
                save_products(products)
                st.success("Barang dihapus dari master.")
                st.rerun()


# ---------------------------------------------------------------------------
# Halaman: Profil Perusahaan
# ---------------------------------------------------------------------------

def _img_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _html(s: str) -> str:
    """Hapus indentasi di awal tiap baris sebelum dikirim ke st.markdown.

    Tanpa ini, baris HTML yang menjorok >=4 spasi (karena mengikuti
    indentasi kode Python) akan dianggap sebagai *code block* oleh parser
    Markdown Streamlit, sehingga HTML tampil sebagai teks mentah, bukan
    dirender. Ini akar masalah dari error yang muncul sebelumnya.
    """
    return "\n".join(line.strip() for line in s.strip("\n").split("\n"))


def page_profil_perusahaan():
    logo_b64 = _img_b64(LOGO_WHITE_PATH) if os.path.exists(LOGO_WHITE_PATH) else (
        _img_b64(LOGO_PATH) if os.path.exists(LOGO_PATH) else ""
    )
    icon_b64 = _img_b64(ICON_PATH) if os.path.exists(ICON_PATH) else ""

    st.markdown(_html(f"""
    <style>
    .tgi-hero {{
        position: relative;
        background: linear-gradient(120deg, {NAVY} 0%, {NAVY_SOFT} 100%);
        margin: -1rem -1rem 36px -1rem;
        padding: 64px 56px;
        border-top: 5px solid {AMBER};
        overflow: hidden;
    }}
    .tgi-hero-watermark {{
        position: absolute;
        top: 50%; right: -60px;
        transform: translateY(-50%);
        width: 480px; opacity: 0.10;
        pointer-events: none;
    }}
    .tgi-hero-inner {{ position: relative; z-index: 1; max-width: 620px; }}
    .tgi-hero-inner img.tgi-logo {{ height: 42px; margin-bottom: 24px; }}
    .tgi-badge {{
        display: inline-block; background: {AMBER}; color: {NAVY};
        font-weight: 700; font-size: 12px; letter-spacing: 1.5px;
        text-transform: uppercase; padding: 6px 14px; margin-bottom: 20px;
    }}
    .tgi-hero-inner h1 {{
        font-size: 46px; font-weight: 800; line-height: 1.15;
        margin: 0; color: #FFFFFF;
    }}
    .tgi-hero-inner h1 span {{ color: {AMBER}; }}
    .tgi-accent {{ display: flex; align-items: center; gap: 8px; margin: 24px 0; }}
    .tgi-accent .dash {{ width: 18px; height: 3px; background: #FFFFFF; }}
    .tgi-accent .bar {{ width: 70px; height: 3px; background: {AMBER}; }}
    .tgi-hero-inner p {{
        font-size: 15.5px; color: #D7D4C8; line-height: 1.7; max-width: 520px;
    }}
    .tgi-section {{ margin-bottom: 48px; }}
    .tgi-section-title {{
        font-size: 26px; font-weight: 700; color: {NAVY}; margin-bottom: 6px;
    }}
    .tgi-section-sub {{
        color: #7A7264; font-size: 14.5px; margin-bottom: 24px; max-width: 640px;
    }}
    .tgi-about-p {{
        color: #4A4638; font-size: 14.5px; line-height: 1.75; max-width: 560px;
    }}
    .tgi-contact-card {{
        background: {CREAM}; padding: 22px 24px; border-left: 4px solid {AMBER};
        font-size: 13.5px; color: #4A4638; line-height: 1.8;
    }}
    .tgi-contact-card .name {{
        font-weight: 700; color: {NAVY}; font-size: 15px; margin-bottom: 10px;
    }}
    .tgi-contact-card a {{ color: {NAVY}; font-weight: 600; text-decoration: none; }}
    .tgi-stats-wrap {{
        display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px;
    }}
    .tgi-stat {{ background: {CREAM}; border-left: 4px solid {AMBER}; padding: 20px 22px; }}
    .tgi-stat .num {{
        font-size: 30px; font-weight: 800; color: {NAVY}; font-family: monospace;
    }}
    .tgi-stat .desc {{ font-size: 13px; color: #7A7264; margin-top: 4px; }}
    .tgi-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
    .tgi-card {{
        background: #FFFFFF; border: 1px solid #E7E2D4; padding: 22px;
        transition: box-shadow .15s, transform .15s;
    }}
    .tgi-card:hover {{ box-shadow: 0 6px 20px rgba(30,36,66,0.10); transform: translateY(-2px); }}
    .tgi-card .icon {{ font-size: 26px; margin-bottom: 10px; }}
    .tgi-card .title {{ font-weight: 700; color: {NAVY}; font-size: 15.5px; margin-bottom: 6px; }}
    .tgi-card .body {{ font-size: 13.5px; color: #7A7264; line-height: 1.55; }}
    .tgi-footer {{
        background: {NAVY}; color: #C9C5B8; padding: 32px 40px;
        margin: 12px -1rem -1rem -1rem; font-size: 13.5px; line-height: 1.7;
    }}
    .tgi-footer b {{ color: #FFFFFF; }}
    .tgi-footer a {{ color: {AMBER}; text-decoration: none; }}
    @media (max-width: 900px) {{
        .tgi-stats-wrap, .tgi-grid {{ grid-template-columns: 1fr; }}
        .tgi-hero-watermark {{ display: none; }}
    }}
    </style>

    <div class="tgi-hero">
        {"<img class='tgi-hero-watermark' src='data:image/png;base64," + icon_b64 + "'/>" if icon_b64 else ""}
        <div class="tgi-hero-inner">
            {"<img class='tgi-logo' src='data:image/png;base64," + logo_b64 + "'/>" if logo_b64 else ""}
            <h1>Empower People,<br/><span>Enrich Lives.</span></h1>
            <div class="tgi-accent"><span class="dash"></span><span class="bar"></span></div>
            <p>Lebih dari sekadar mengirimkan produk berkualitas, kami berkomitmen
            memberikan pengalaman terbaik dan menjaga performa yang konsisten
            dalam setiap layanan kami.</p>
        </div>
    </div>
    """), unsafe_allow_html=True)

    # --- Tentang Kami -------------------------------------------------------
    left, right = st.columns([1.3, 1])
    with left:
        st.markdown(_html("""
        <div class="tgi-section-title">Tentang Kami</div>
        <p class="tgi-about-p">
        PT Tanaka Graha Indonesia berawal sebagai perusahaan distributor dan
        retail yang menyediakan berbagai produk <i>chilled</i> dan
        <i>frozen</i>, termasuk daging sapi premium, seafood, dan produk
        lainnya dari berbagai negara.<br/><br/>
        Dengan dedikasi tinggi, kami berkomitmen menghadirkan produk
        berkualitas dengan harga terjangkau, memperkaya kehidupan, dan
        memberdayakan masyarakat.
        </p>
        """), unsafe_allow_html=True)
    with right:
        st.markdown(_html(f"""
        <div class="tgi-contact-card">
            <div class="name">{COMPANY['name']}</div>
            {COMPANY['location']}<br/>
            {COMPANY['address']}<br/><br/>
            ✉️ {COMPANY['email']}<br/>
            📷 <a href="{COMPANY['instagram']}">Instagram @tanakagraha</a>
        </div>
        """), unsafe_allow_html=True)

    st.write("")

    # --- Statistik ------------------------------------------------------------
    stats_html = "".join(
        f'<div class="tgi-stat"><div class="num">{num}</div>'
        f'<div class="desc">{desc}</div></div>'
        for num, desc in STATS
    )
    st.markdown(
        _html(f'<div class="tgi-section tgi-stats-wrap">{stats_html}</div>'),
        unsafe_allow_html=True,
    )

    # --- Why Us -----------------------------------------------------------
    st.markdown(_html("""
    <div class="tgi-section-title">Why Us?</div>
    <div class="tgi-section-sub">Lebih dari sekadar mengirimkan produk
    berkualitas, kami menjaga performa yang konsisten di setiap layanan.</div>
    """), unsafe_allow_html=True)
    why_html = "".join(
        f'<div class="tgi-card"><div class="icon">{icon}</div>'
        f'<div class="title">{title}</div><div class="body">{body}</div></div>'
        for icon, title, body in WHY_US
    )
    st.markdown(
        _html(f'<div class="tgi-section tgi-grid">{why_html}</div>'),
        unsafe_allow_html=True,
    )

    # --- Layanan Kami -------------------------------------------------------
    st.markdown(_html("""
    <div class="tgi-section-title">Layanan Kami</div>
    <div class="tgi-section-sub">Menyediakan berbagai produk daging dan
    seafood premium untuk kebutuhan retail online maupun offline.</div>
    """), unsafe_allow_html=True)
    svc_html = "".join(
        f'<div class="tgi-card"><div class="icon">{icon}</div>'
        f'<div class="title">{title}</div><div class="body">{body}</div></div>'
        for icon, title, body in SERVICES
    )
    st.markdown(
        _html(f'<div class="tgi-section tgi-grid">{svc_html}</div>'),
        unsafe_allow_html=True,
    )

    # --- Footer ---------------------------------------------------------------
    st.markdown(_html(f"""
    <div class="tgi-footer">
        <b>{COMPANY['name']}</b><br/>
        {COMPANY['location']}<br/>
        {COMPANY['address']}<br/><br/>
        {COMPANY['email']} &nbsp;·&nbsp;
        <a href="{COMPANY['instagram']}">Instagram</a>
    </div>
    """), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

if page == "Profil Perusahaan":
    page_profil_perusahaan()
elif page == "Dashboard":
    page_dashboard()
elif page == "Input Pesanan":
    page_input_pesanan()
elif page == "Daftar Pesanan":
    page_daftar_pesanan()
elif page == "Master Barang":
    page_master_barang()
