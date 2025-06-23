from amaranth import *
from amaranth.build import Attrs, Pins, Resource


class BlinkLeds(Elaboratable):
    def elaborate(self, platform):
        m = Module()

        column = platform.request("column", 0, dir="o").o
        row = platform.request("row", 0, dir="o").o
        leds = [platform.request("led", i, dir="o") for i in range(8)]
        leds = Cat([led.o for led in leds])

        timer = Signal(unsigned(26))
        m.d.sync += timer.eq(timer + 1)

        csig = Signal(7, init=0b1)
        rsig = Signal(5, init=0b11110)
        m.d.comb += column.eq(csig)
        m.d.comb += row.eq(rsig)
        m.d.comb += leds.eq(csig)

        with m.If(timer == 0):
            m.d.sync += csig.eq(csig.rotate_left(1))
            with m.If(csig.rotate_left(1) == csig.init):
                m.d.sync += rsig.eq(rsig.rotate_left(1))

        return m
    
if __name__ ==  "__main__":
    from alchitry_cu import AlchitryCuPlatform
    column = ['E14', 'C14', 'C1', 'D3', 'G1', 'A6', 'A3']
    row = ['A12', 'A1', 'A10', 'C9', 'E1']
    column = " ".join(column)
    row = " ".join(row)
    platform = AlchitryCuPlatform()

    platform.add_resources([
                               Resource("column", 0, Pins(column, dir="o"), Attrs(IO_STANDARD="LVCMOS")),
                               Resource("row", 0, Pins(row, dir="o"), Attrs(IO_STANDARD="LVCMOS"))
                           ])

    platform.build(BlinkLeds(), do_program=True)
