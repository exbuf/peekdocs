// Verilog test file for peekdocs
module sample(input clk, output reg q);
    always @(posedge clk) q <= ~q;
endmodule
