import streamlit as st
import pandas as pd
import json

# --- Page Config ---
st.set_page_config(page_title="Trade Tracker", page_icon="📈", layout="wide")

st.title("📊 Trade Tracker")
st.caption("Log your trades, track performance, and analyze results.")

# --- Helper to Load Trades from JSON ---
def load_trades(uploaded_file):
    try:
        data = json.load(uploaded_file)
        st.session_state["loaded_trades"] = data
        st.success("✅ Trades successfully loaded!")
    except Exception as e:
        st.error(f"Failed to load trades: {e}")

# --- Tabs ---
tab1, tab2 = st.tabs(["💼 Trade Tracker", "📈 Overview"])

# ======================================================
# TAB 1: TRADE TRACKER
# ======================================================
with tab1:
    left, right = st.columns([3, 1])

    with left:
        # Load previous trades if available
        if "loaded_trades" in st.session_state:
            prev_trades = st.session_state["loaded_trades"]
            num_trades = len(prev_trades)
        else:
            prev_trades = []
            num_trades = 1

        num_trades = st.number_input(
            "How many trades did you make?", min_value=1, max_value=50, value=num_trades, step=1
        )

        st.divider()

        trades = []
        total_profit = 0.0
        total_investment = 0.0
        portfolio_value = 0.0

        for i in reversed(range(1, num_trades + 1)):
            prev = next((t for t in prev_trades if t["Trade"] == i), None)
            with st.expander(f"Trade {i}", expanded=True):
                col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

                with col1:
                    buy_price = st.number_input(
                        "Buy Price", min_value=0.0, step=0.01, key=f"buy_{i}",
                        value=prev["Buy"] if prev else 0.0
                    )
                with col2:
                    sell_price = st.number_input(
                        "Sell Price", min_value=0.0, step=0.01, key=f"sell_{i}",
                        value=prev["Sell"] if prev else 0.0
                    )
                with col3:
                    fee = st.number_input(
                        "Market Fee (%)", min_value=0.0, step=0.1, key=f"fee_{i}",
                        value=prev["Fee (%)"] if prev else 0.0
                    )
                with col4:
                    color = st.selectbox(
                        "Color", ["default", "red", "blue"], key=f"color_{i}",
                        index=(["default", "red", "blue"].index(prev["Color"]) if prev else 0)
                    )

                # --- Calculations ---
                profit = (sell_price - buy_price) - (sell_price * fee / 100)
                roi = (profit / buy_price * 100) if buy_price > 0 else 0
                total_return = sell_price - (sell_price * fee / 100)

                total_profit += profit
                total_investment += buy_price

                trades.append({
                    "Trade": i,
                    "Buy": buy_price,
                    "Sell": sell_price,
                    "Fee (%)": fee,
                    "Profit": profit,
                    "ROI (%)": roi,
                    "Total Return": total_return,
                    "Color": color
                })

        # Save to session for other tab
        st.session_state["trades"] = trades

    with right:
        st.subheader("📊 Totals Overview")
        st.divider()

        # --- Portfolio Logic ---
        portfolio_value = 0.0
        prev_portfolio = 0.0
        total_added_capital = 0.0
        initialized = False

        for t in reversed(trades):
            buy = t["Buy"]
            sell = t["Sell"]
            fee = t["Fee (%)"]
            net_result = (sell - buy) - (sell * fee / 100)

            if not initialized:
                prev_portfolio = buy
                portfolio_value = buy + net_result
                initialized = True
            else:
                if buy > prev_portfolio:
                    added_capital = buy - prev_portfolio
                    total_added_capital += added_capital
                else:
                    added_capital = 0
                portfolio_value = prev_portfolio - buy + net_result + added_capital
            prev_portfolio = portfolio_value

        effective_invested = (trades[-1]["Buy"] if trades else 0) + total_added_capital
        total_roi = ((portfolio_value / effective_invested) - 1) * 100 if effective_invested > 0 else 0

        st.metric("💰 Total Profit", f"${total_profit:,.2f}")
        st.metric("📈 Total ROI", f"{total_roi:,.2f}%")
        st.metric("💼 Portfolio Value", f"${portfolio_value:,.2f}")

        st.divider()
        st.subheader("💾 Save / Load")

        # --- Save Button ---
        if st.button("💾 Save Trades"):
            json_data = json.dumps(trades, indent=4)
            st.download_button(
                "⬇️ Download JSON File",
                data=json_data,
                file_name="trades_backup.json",
                mime="application/json"
            )

        # --- Load Button ---
        uploaded = st.file_uploader("📂 Upload Saved Trades (.json)", type=["json"])
        if uploaded is not None:
            load_trades(uploaded)

# ======================================================
# TAB 2: OVERVIEW
# ======================================================
with tab2:
    st.header("📋 Trade Overview")
    trades = st.session_state.get("trades", [])

    if not trades:
        st.info("No trades added yet. Go to the Trade Tracker tab to enter your trades.")
    else:
        df = pd.DataFrame(trades)
        df = df.sort_values(by="Trade", ascending=True).reset_index(drop=True)

        st.subheader("📊 Performance View")
        mode = st.radio("View Mode:", ["All Trades", "Split by Color"], horizontal=True)

        def format_table(df_input):
            df_display = df_input.copy()
            df_display["Buy"] = df_display["Buy"].map("${:,.2f}".format)
            df_display["Sell"] = df_display["Sell"].map("${:,.2f}".format)
            df_display["Profit"] = df_display["Profit"].map("${:,.2f}".format)
            df_display["Total Return"] = df_display["Total Return"].map("${:,.2f}".format)
            df_display["ROI (%)"] = df_display["ROI (%)"].map("{:,.2f}%".format)
            df_display["Fee (%)"] = df_display["Fee (%)"].map("{:,.2f}%".format)
            return df_display

        def show_charts(df_subset, label="All Trades"):
            st.markdown(f"### {label}")
            chart_df = df_subset.sort_values(by="Trade", ascending=True)
            chart_df["Portfolio Value"] = chart_df["Buy"].cumsum() + chart_df["Profit"].cumsum()
            st.markdown("**💰 Profit per Trade**")
            st.bar_chart(chart_df.set_index("Trade")["Profit"])
            st.markdown("**💼 Portfolio Value Growth**")
            st.line_chart(chart_df.set_index("Trade")["Portfolio Value"])
            st.markdown("**📈 ROI per Trade (%)**")
            st.bar_chart(chart_df.set_index("Trade")["ROI (%)"])

        if mode == "All Trades":
            st.dataframe(format_table(df), use_container_width=True)
            show_charts(df)
        else:
            red_df = df[df["Color"] == "red"]
            blue_df = df[df["Color"] == "blue"]

            st.markdown("### 🔍 Trade Tables by Color")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 🔴 Red Trades")
                if len(red_df):
                    st.dataframe(format_table(red_df), use_container_width=True)
                else:
                    st.info("No red trades available.")
            with col2:
                st.markdown("#### 🔵 Blue Trades")
                if len(blue_df):
                    st.dataframe(format_table(blue_df), use_container_width=True)
                else:
                    st.info("No blue trades available.")

            st.divider()
            st.markdown("### 📊 Performance by Color")
            col3, col4 = st.columns(2)
            with col3:
                if len(red_df):
                    show_charts(red_df, "🔴 Red Trades")
                else:
                    st.info("No red trades available.")
            with col4:
                if len(blue_df):
                    show_charts(blue_df, "🔵 Blue Trades")
                else:
                    st.info("No blue trades available.")

        st.caption("Charts and tables update automatically as you adjust or load your trades.")
