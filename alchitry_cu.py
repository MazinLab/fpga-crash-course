import os
import subprocess

from amaranth.build import *
from amaranth.vendor import LatticeICE40Platform
from amaranth_boards.resources import *

__all__ = ["AlchitryCuPlatform"]

column = ['E14', 'C14', 'C1', 'D3', 'G1', 'A6', 'A3']
row = ['A12', 'A1', 'A10', 'C9', 'E1']
column = " ".join(column)
row = " ".join(row)

class AlchitryCuPlatform(LatticeICE40Platform):
    device      = "iCE40HX8K"
    package     = "CB132"
    speed       = "1"
    default_clk = "clk100"
    resources   = [
        Resource(
            "clk100", 0, Pins("P7", dir="i"), Clock(100e6), Attrs(GLOBAL=True,
            IO_STANDARD="SB_LVCMOS")
        ),

        Resource("usb", 0,
            Subsignal("usb_tx", Pins("P14", dir="o")),
            Subsignal("usb_rx", Pins("M9", dir="i")),
            Attrs(IO_STANDARD="LVCMOS")
        ),
       Resource("column", 0, Pins(column, dir="o"), Attrs(IO_STANDARD="LVCMOS")),
       Resource("row", 0, Pins(row, dir="o"), Attrs(IO_STANDARD="LVCMOS")),

        *SPIFlashResources(0,
            cs_n="P13", clk="P12", copi="M11", cipo="P11",
            attrs=Attrs(IO_STANDARD="SB_LVCMOS")
        ),

        *LEDResources(
            pins="J11 K11 K12 K14 L12 L14 M12 N14", attrs=Attrs(IO_STANDARD="SB_LVCMOS")
        ) 
    ]

    connectors  = [
        Connector("bank", 0, "M1  L1  J1  J3  G1  G3  E1  D1  C1  B1  D3  C3  A1  A2  A3  A4"
                             "P1  N1  K4  K3  H3  H1  G4  H4  F3  F4  E4  D4  C4  D5  C5  A5"),
        Connector("bank", 1, "A6  A7  A10 A11 C9  C10 A12 B14 C14 D14 E14 E12 F14 G14 H12 J12"
                             "C6  C7  D6  D7  D9  D10 C11 C12 D11 D12 E11 F11 F12 G12 G11 H11"),

        Connector("bank", 2, "M3  M4  L4  L5  M6  M7  L9  -   -   -   -   -   -   -   -   -  "
                             "P2  P3  P4  P5  L6  L8  P10 -   -   -   -   -   -   -   -   -  ")
    ]

    def toolchain_program(self, products, name):
        iceprog = os.environ.get("ICEPROG", "iceprog")
        with products.extract("{}.bin".format(name)) as bitstream_filename:
            # TODO: this should be factored out and made customizable
            subprocess.check_call([iceprog, bitstream_filename])

if __name__ ==  "__main__":
    from amaranth_boards.test.blinky import Blinky
    AlchitryCuPlatform().build(Blinky(), do_program=True)

