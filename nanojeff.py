from amaranth import *
from amaranth.sim import Simulator
from amaranth.back import rtlil, verilog
from amaranth.lib.memory import Memory
from amaranth.lib.wiring import Component, In, Out
from amaranth.lib import enum

# TODO: Fill out the rest of this table
# https://github.com/ld-cd/nanojeff?tab=readme-ov-file#instruction-table
class OpCode(enum.Enum, shape=4):
    SL  = 0b0000
    SR  = 0b0001

class NanoJeffCPU(Component):
    """
    This CPU should implement the ISA described here: https://github.com/ld-cd/nanojeff

    For simplicity the read side of both buses is combinatorial

    Attributes
    ----------
    instruction : Signal, in
        The 8 bit instruction comes in here, on the same cycle
        it's address is raised on the addres sport
    instruction_address : Signal, out
        The 8 bit address for the current instruction
    data_in : Signal, in
        Data in from the data bus, has the same symantics as
        the instruction bus, state is undefined when
        ``data_write`` is raised.
    data_out : Signal, out
        When ``data_write`` is raised, the data on this port
        will be written to the memory on the following cycle
    data_write : Signal, out
        See above
    data_address : Signal, out
        The address to read/write to
    """
    instruction: In(8)
    instruction_address: Out(8)

    data_in: In(8)
    data_out: Out(8)
    data_write: Out(1)
    data_address: Out(8)

    def elaborate(self, platform):
        m = Module()

        # Like verilog, amaranth is last assignment wins.
        # By default we just increment the ``program_counter``
        # You can override this later if you encounter a branch
        program_counter = Signal(8)
        m.d.sync += program_counter.eq(program_counter + 1)
        m.d.comb += self.instruction_address.eq(program_counter)

        # Here's a memory holding the four nanojeff CPU registers
        m.submodules.regfile = regfile = Memory(shape=unsigned(8), depth=4, init=[])

        # TODO: what domain do you want this to be in, sync or comb?
        # (Both can be correct depending on your implementation strat)
        # Do you need one read port or two?
        #
        #reg_read = regfile.read_port(domain="...")
        reg_write = regfile.write_port(domain="sync")

        # Instruction Decode per the table and format
        opcode = Signal(OpCode)
        m.d.comb += opcode.eq(self.instruction[4:])
        # TODO: Decode the ``a`` and ``b`` registers and ``imm``

        # You can implement the main logic of the CPU in
        # this switch case here, so TODO: Fill this out
        # (Or you can choose another aproach)
        with m.Switch(opcode):
            with m.Case(OpCode.SL):
                pass
            with m.Case(OpCode.SR):
                pass

        return m


class Harness(Component):
    """
    A simple test harness with one IO port at address 255

    Parameters
    ----------
    program : list[int]
        The program to load into the program rom

    Attributes
    ----------
    leds : Signal, out
        The output io port at address 255
    buttons : Signal, in
        The input io port at address 255
    """
    leds: Out(8)
    buttons: In(8)

    def __init__(self, program):
        self.program = program
        super().__init__()

    def elaborate(self, platform):
        m = Module()

        # Instantiate the CPU
        m.submodules.cpu = cpu = NanoJeffCPU()

        # Memories for data and instructions
        m.submodules.dmem = dmem = Memory(shape=unsigned(8), depth=256, init=[])
        m.submodules.imem = imem = Memory(shape=unsigned(8), depth=256, init=self.program)

        dportr = dmem.read_port(domain="comb")
        dportw = dmem.write_port(domain="sync")
        iport = imem.read_port(domain="comb")

        m.d.comb += [
            dportr.addr.eq(cpu.data_address),
            dportw.addr.eq(cpu.data_address),
            dportw.en.eq(cpu.data_write),
            cpu.data_in.eq(dportr.data),
            dportw.data.eq(cpu.data_out),
            iport.addr.eq(cpu.instruction_address),
            cpu.instruction.eq(iport.data),
        ]

        # Data address 255 is the IO port
        with m.If(cpu.data_address == 255):
            m.d.comb += cpu.data_in.eq(self.buttons)
            with m.If(cpu.data_write == 1):
                m.d.sync += self.leds.eq(cpu.data_out)

        return m


# Bonus TODO: Implement an assembler
# https://github.com/ld-cd/NanoJeff/blob/master/tests/increment_mem.s
increment_leds = [
    0b01010000,
    0b01010101,
    0b01011010,
    0b01011111,
    0b10101111,
    0b10111111,
    0b01101100,
    0b01010000,
    0b10011100,
    0b10100001,
    0b01100100,
    0b10011100,
    0b01100001,
    0b11110001,
]
m = Harness(increment_leds)

async def testbench(ctx):
    leds_last = 0
    for cycle in range(64):
        await ctx.tick()
        leds = ctx.get(m.leds)
        if ctx.get(m.leds) != leds_last:
            print(f"cycle: {cycle:04d} leds: {leds_last:08b}=>{leds:08b}")
            leds_last = leds

sim = Simulator(m)
sim.add_clock(1e-6)
sim.add_testbench(testbench)

try:
    import amaranth_playground
    with amaranth_playground.show_waveforms(sim):
        sim.run()

    amaranth_playground.show_verilog(verilog.convert(m, ports=[m.leds, m.buttons]))
    amaranth_playground.show_rtlil(rtlil.convert(m, ports=[m.leds, m.buttons]))
except Exception:
    open("nanojeff.v", "w").write(verilog.convert(m, ports=[m.leds, m.buttons]))
    open("nanojeff.rtlil", "w").write(rtlil.convert(m, ports=[m.leds, m.buttons]))
    with sim.write_vcd("nanojeff.vcd"):
        sim.run()
