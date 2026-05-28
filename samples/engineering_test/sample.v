// sample.v -- Verilog: SPI master controller
// PEEKDOCS_TEST_MARKER

module spi_master #(
    parameter CLK_DIV = 8,
    parameter DATA_WIDTH = 8
)(
    input  wire                  clk,
    input  wire                  rst_n,
    input  wire                  start,
    input  wire [DATA_WIDTH-1:0] tx_data,
    output reg  [DATA_WIDTH-1:0] rx_data,
    output reg                   busy,
    output reg                   sclk,
    output reg                   mosi,
    input  wire                  miso,
    output reg                   cs_n
);

    reg [$clog2(CLK_DIV)-1:0]   clk_cnt;
    reg [$clog2(DATA_WIDTH)-1:0] bit_cnt;
    reg [DATA_WIDTH-1:0]         shift_reg;
    reg [1:0]                    state;

    localparam IDLE = 2'b00, TRANSFER = 2'b01, DONE = 2'b10;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state    <= IDLE;
            busy     <= 1'b0;
            cs_n     <= 1'b1;
            sclk     <= 1'b0;
        end else case (state)
            IDLE: if (start) begin
                shift_reg <= tx_data;
                bit_cnt   <= DATA_WIDTH - 1;
                clk_cnt   <= 0;
                cs_n      <= 1'b0;
                busy      <= 1'b1;
                state     <= TRANSFER;
            end
            TRANSFER: begin
                clk_cnt <= clk_cnt + 1;
                if (clk_cnt == CLK_DIV/2 - 1) sclk <= 1'b1;
                if (clk_cnt == CLK_DIV - 1) begin
                    sclk <= 1'b0;
                    clk_cnt <= 0;
                    shift_reg <= {shift_reg[DATA_WIDTH-2:0], miso};
                    if (bit_cnt == 0) state <= DONE;
                    else bit_cnt <= bit_cnt - 1;
                end
                mosi <= shift_reg[DATA_WIDTH-1];
            end
            DONE: begin
                rx_data <= shift_reg;
                cs_n    <= 1'b1;
                busy    <= 1'b0;
                state   <= IDLE;
            end
        endcase
    end

endmodule
