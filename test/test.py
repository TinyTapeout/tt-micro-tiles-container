# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge


@cocotb.test()
async def test_proj1(dut):
    dut._log.info("Start")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0  # Select the first project, which is a multiplier module
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Test multiplier module")

    assert dut.uo_out.value == 0
    for x in range(16):
        for y in range(16):
            dut.ui_in.value = (x << 4) | y
            await ClockCycles(dut.clk, 1)
            await FallingEdge(dut.clk)
            assert dut.uo_out.value == x * y


@cocotb.test()
async def test_proj2(dut):
    dut._log.info("Start")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 1  # Select the second project, which xors the input with 0x55
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Test xor with 0x55 module")

    assert dut.uo_out.value == 0
    for x in range(256):
        dut.ui_in.value = x
        await ClockCycles(dut.clk, 1)
        await FallingEdge(dut.clk)
        assert dut.uo_out.value == x ^ 0x55


@cocotb.test()
async def test_proj3(dut):
    dut._log.info("Start")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 2  # Select the third project, which xors the input with 0x42
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Test xor with 0x42 module")

    assert dut.uo_out.value == 0
    for x in range(256):
        dut.ui_in.value = x
        await ClockCycles(dut.clk, 1)
        await FallingEdge(dut.clk)
        assert dut.uo_out.value == x ^ 0x42


@cocotb.test()
async def test_proj4(dut):
    dut._log.info("Start")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 3  # Select the fourth project, echos the input on reset and outputs a counter otherwise
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)

    dut._log.info("Test input echo on reset")

    assert dut.uo_out.value == 0
    for x in range(256):
        dut.ui_in.value = x
        await ClockCycles(dut.clk, 1)
        await FallingEdge(dut.clk)
        assert dut.uo_out.value == x

    dut._log.info("Test counter")
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)
    for x in range(256):
        await FallingEdge(dut.clk)
        assert dut.uo_out.value == x
        await ClockCycles(dut.clk, 1)
