// SPDX-License-Identifier: Apache-2.0
// Copyright (C) 2024, Tiny Tapeout LTD

`default_nettype none

// This project XORs the input with 0x42 on each clock cycle

module tt_um_micro_proj3 (
`ifdef USE_POWER_PINS
    input  wire       VPWR,
    input  wire       VGND,
`endif
    input  wire [7:0] ui_in,   // Dedicated inputs
    output reg  [7:0] uo_out,  // Dedicated outputs
    input  wire       clk,     // clock
    input  wire       rst_n    // reset_n - low to reset
);

  always @(posedge clk or negedge rst_n) begin
`ifdef USE_POWER_PINS
    if (~VPWR | VGND) begin
      uo_out <= 8'h00;
    end else
`endif
    if (~rst_n) begin
      uo_out <= 8'h00;
    end else begin
      uo_out <= ui_in ^ 8'h42;
    end
  end
  
endmodule  // tt_um_micro_proj3
