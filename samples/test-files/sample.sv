// SystemVerilog test file for peekdocs
module sample(input logic clk, output logic q);
    always_ff @(posedge clk) q <= ~q;
endmodule
