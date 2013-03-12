from migen.fhdl.structure import *
from migen.fhdl.specials import Instance
from migen.fhdl.module import Module
from migen.bank.description import *
from migen.bank.eventmanager import *
from migen.bus import wishbone

_count_width = 11

class MiniMAC(Module, AutoReg):
	def __init__(self):
		# PHY signals
		self.phy_tx_clk = Signal()
		self.phy_tx_data = Signal(4)
		self.phy_tx_en = Signal()
		self.phy_tx_er = Signal()
		self.phy_rx_clk = Signal()
		self.phy_rx_data = Signal(4)
		self.phy_dv = Signal()
		self.phy_rx_er = Signal()
		self.phy_col = Signal()
		self.phy_crs = Signal()
		self.phy_rst_n = Signal()
		
		# CPU interface
		self._phy_reset = RegisterField(reset=1)
		self._rx_count_0 = RegisterField(_count_width, access_bus=READ_ONLY, access_dev=WRITE_ONLY)
		self._rx_count_1 = RegisterField(_count_width, access_bus=READ_ONLY, access_dev=WRITE_ONLY)
		self._tx_count = RegisterField(_count_width, access_dev=READ_WRITE)
		self._tx_start = RegisterRaw()
		
		self.submodules.ev = EventManager()
		self.ev.rx0 = EventSourcePulse()
		self.ev.rx1 = EventSourcePulse()
		self.ev.tx = EventSourcePulse()
		self.ev.finalize()
		
		self.membus = wishbone.Interface()
		
		###

		init = Signal(reset=1)
		self.sync += init.eq(0)
		rx_ready_0 = Signal()
		rx_ready_1 = Signal()
		rx_pending_0 = self.ev.rx0.pending
		rx_pending_1 = self.ev.rx1.pending
		rx_pending_0_r = Signal()
		rx_pending_1_r = Signal()
		self.comb += [
			self.phy_rst_n.eq(~self._phy_reset.field.r),
			
			rx_ready_0.eq(init | (rx_pending_0_r & ~rx_pending_0)),
			rx_ready_1.eq(init | (rx_pending_1_r & ~rx_pending_1)),
			
			self._tx_count.field.w.eq(0),
			self._tx_count.field.we.eq(self.ev.tx.trigger)
		]
		self.sync += [
			rx_pending_0_r.eq(rx_pending_0),
			rx_pending_1_r.eq(rx_pending_1)
		]
		self.specials += Instance("minimac3",
				Instance.ClockPort("sys_clk"),
				Instance.ResetPort("sys_rst"),

				Instance.Output("rx_done_0", self.ev.rx0.trigger),
				Instance.Output("rx_count_0", self._rx_count_0.field.w),
				Instance.Output("rx_done_1", self.ev.rx1.trigger),
				Instance.Output("rx_count_1", self._rx_count_1.field.w),
				Instance.Input("rx_ready_0", rx_ready_0),
				Instance.Input("rx_ready_1", rx_ready_1),

				Instance.Input("tx_start", self._tx_start.re),
				Instance.Input("tx_count", self._tx_count.field.r),
				Instance.Output("tx_done", self.ev.tx.trigger),
				
				Instance.Input("wb_adr_i", self.membus.adr),
				Instance.Input("wb_dat_i", self.membus.dat_w),
				Instance.Input("wb_sel_i", self.membus.sel),
				Instance.Input("wb_stb_i", self.membus.stb),
				Instance.Input("wb_cyc_i", self.membus.cyc),
				Instance.Input("wb_we_i", self.membus.we),
				Instance.Output("wb_dat_o", self.membus.dat_r),
				Instance.Output("wb_ack_o", self.membus.ack),
				
				Instance.ClockPort("phy_tx_clk", "eth_tx"),
				Instance.Output("phy_tx_data", self.phy_tx_data),
				Instance.Output("phy_tx_en", self.phy_tx_en),
				Instance.Output("phy_tx_er", self.phy_tx_er),
				Instance.ClockPort("phy_rx_clk", "eth_rx"),
				Instance.Input("phy_rx_data", self.phy_rx_data),
				Instance.Input("phy_dv", self.phy_dv),
				Instance.Input("phy_rx_er", self.phy_rx_er),
				Instance.Input("phy_col", self.phy_col),
				Instance.Input("phy_crs", self.phy_crs))
