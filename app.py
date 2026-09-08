"""
TGI WMS - Warehouse Management System sederhana
Data source: file CSV (data/customers.csv, data/products.csv,
             data/orders.csv, data/order_items.csv)

Cara menjalankan:
    pip install -r requirements.txt
    streamlit run app.py
"""

import os
import uuid
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

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
    "Dikirim": "#D98E2C",
    "Selesai": "#3F6B33",
}

st.set_page_config(page_title="TGI WMS", page_icon="📦", layout="wide")

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

st.sidebar.markdown(
    """
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
        <div style="background:#D98E2C;color:#1C2B33;font-weight:700;
                    padding:6px 10px;font-size:13px;">TGI</div>
        <div>
            <div style="font-weight:600;font-size:14px;color:#1C2B33;">TGI Warehouse</div>
            <div style="font-size:11px;color:#7A7264;">Management System</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.divider()

page = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Input Pesanan", "Daftar Pesanan", "Master Barang"],
    label_visibility="collapsed",
)

st.sidebar.divider()
st.sidebar.caption("Gudang Pusat — Cikarang")
st.sidebar.caption(f"Sumber data: folder `data/` (CSV)")

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

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Pesanan", f"{total_pesanan}")
    with col2:
        st.metric("Stock Tersedia", f"{stock_tersedia:,} unit".replace(",", "."))

    st.write("")
    row1_left, row1_right = st.columns(2)

    # --- Grafik: Pesanan per Status ---------------------------------------
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
            fig = px.bar(
                status_counts, x="status", y="jumlah", color="status",
                color_discrete_map=STATUS_COLOR, text="jumlah",
            )
            fig.update_traces(textposition="outside", showlegend=False)
            fig.update_layout(
                **CHART_LAYOUT, showlegend=False,
                xaxis_title=None, yaxis_title="Jumlah Pesanan",
            )
            st.plotly_chart(fig, use_container_width=True)

    # --- Grafik: Trend Pesanan Harian --------------------------------------
    with row1_right:
        st.subheader("Trend Pesanan Harian")
        if orders.empty:
            st.info("Belum ada pesanan.")
        else:
            trend = orders.groupby("order_date").size().reset_index(name="jumlah")
            trend["order_date"] = pd.to_datetime(trend["order_date"])
            trend = trend.sort_values("order_date")
            fig = px.line(trend, x="order_date", y="jumlah", markers=True)
            fig.update_traces(line_color="#2C5F8A", marker=dict(size=8, color="#2C5F8A"))
            fig.update_layout(
                **CHART_LAYOUT, xaxis_title=None, yaxis_title="Jumlah Pesanan",
            )
            st.plotly_chart(fig, use_container_width=True)

    row2_left, row2_right = st.columns(2)

    # --- Grafik: Stock per Barang -------------------------------------------
    with row2_left:
        st.subheader("Stock per Barang")
        if products.empty:
            st.info("Belum ada data barang.")
        else:
            stock_df = products[["name", "stock"]].sort_values("stock")
            colors = ["#A3402E" if s < 200 else "#1F6F5C" for s in stock_df["stock"]]
            fig = px.bar(
                stock_df, x="stock", y="name", orientation="h", text="stock",
            )
            fig.update_traces(marker_color=colors, textposition="outside")
            fig.update_layout(
                **CHART_LAYOUT, xaxis_title="Stock", yaxis_title=None,
            )
            st.plotly_chart(fig, use_container_width=True)

    # --- Grafik: Item Terlaris ----------------------------------------------
    with row2_right:
        st.subheader("Item Terlaris (berdasarkan Qty Dipesan)")
        if order_items.empty:
            st.info("Belum ada item pesanan.")
        else:
            item_qty = (
                order_items.groupby("product_id")["qty"].sum().reset_index()
                .merge(products[["product_id", "name"]], on="product_id", how="left")
                .sort_values("qty", ascending=False).head(5)
            )
            fig = px.bar(
                item_qty, x="name", y="qty", text="qty",
                color_discrete_sequence=["#D98E2C"],
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                **CHART_LAYOUT, xaxis_title=None, yaxis_title="Total Qty Dipesan",
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
# Router
# ---------------------------------------------------------------------------

if page == "Dashboard":
    page_dashboard()
elif page == "Input Pesanan":
    page_input_pesanan()
elif page == "Daftar Pesanan":
    page_daftar_pesanan()
elif page == "Master Barang":
    page_master_barang()
