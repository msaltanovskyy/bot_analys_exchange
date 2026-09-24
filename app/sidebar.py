class ConfigSidebar:

  symbols: list[str]
  available_timeframes: list
  timeframes: str
  limit: int
  is_auto_trade: bool
  market_type: str | None  = None
  order_type: str | None = None

  def sidebar_main_frame(self, st, markets):

    st.sidebar.title("Market Analyzer")

    available_timeframes = [
      "1m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"
    ]
    available_market_types = ['Future', 'Spot']
    available_order_types = ['Limit', 'Market']

    symbols = st.sidebar.multiselect(
      "Symbols",
      markets,
      default=markets[:2] if markets else [],
      max_selections= 10,
    )

    timeframes = st.sidebar.multiselect(
      "Timeframes",
      available_timeframes,
      default=["15m", "1h", "4h"] if available_timeframes else [],
      max_selections= 3,
    )

    if len(timeframes) != 3:
      st.sidebar.error("Timeframes can have only 3 elements.")
      st.stop()

    is_auto_trade = st.sidebar.checkbox(
      "Auto Trade (FOR TESTNET)"
    )

    market_type = st.sidebar.selectbox(
        "Market Type",
        available_market_types,
        placeholder= 'Select market type',
      )

    order_type = st.sidebar.selectbox(
        "Order Type",
        available_order_types,
        placeholder= 'Select order type',
      )

    self.market_type = market_type.lower()
    self.order_type = order_type.lower()


    limit = st.sidebar.slider(label= "Limit",min_value=300, max_value=1000, step=50, value=300)

    self.timeframes = timeframes
    self.symbols = symbols
    self.available_timeframes = available_timeframes
    self.limit = limit

  def sidebar_buttons(self,st,start_scheduler,stop_scheduler):

    col1, col2 = st.sidebar.columns(2)

    with col1:
      if st.button(
        "▶ Start",
        disabled=st.session_state.running,
        width='stretch',
      ):
        if not self.symbols:
          st.error("Select at least one symbol.")
        elif not self.timeframes:
          st.error("Select at least one timeframe.")
        else:
          with st.session_state.lock:
            st.session_state.results.clear()
          start_scheduler()
          st.rerun()

    with col2:
      if st.button(
        "■ Stop",
        disabled=not st.session_state.running,
        width='stretch',
      ):
        stop_scheduler()
        st.rerun()
