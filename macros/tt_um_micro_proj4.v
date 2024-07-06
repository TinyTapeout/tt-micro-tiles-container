// SPDX-License-Identifier: Apache-2.0
// Copyright (C) 2024, Tiny Tapeout LTD

`default_nettype none

// This project is like the factory test - counting up on each clock cycle or mirroring the input on reset

module tt_um_micro_proj4 (
`ifdef USE_POWER_PINS
    input  wire       VPWR,
    input  wire       VGND,
`endif
    input  wire [7:0] ui_in,   // Dedicated inputs
    output wire [7:0] uo_out,  // Dedicated outputs
    input  wire       clk,     // clock
    input  wire       rst_n    // reset_n - low to reset
);

  reg rst_n_i;
  reg [7:0] cnt;

  always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
      rst_n_i <= 1'b0;
    end else begin
      rst_n_i <= 1'b1;
    end
  end

  always @(posedge clk or negedge rst_n_i) begin
    if (~rst_n_i) begin
      cnt <= 0;
    end else begin
      cnt <= cnt + 1;
    end
  end

`ifdef USE_POWER_PINS
  assign uo_out = (~VPWR | VGND) ? 8'h00 : rst_n ? cnt : ui_in;
`else
  assign uo_out = rst_n ? cnt : ui_in;
`endif

endmodule  // tt_um_micro_proj4
