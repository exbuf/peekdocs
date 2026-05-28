-- sample.vhd -- VHDL: 8-bit up/down counter with load
-- PEEKDOCS_TEST_MARKER

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity counter_8bit is
    port (
        clk      : in  std_logic;
        rst      : in  std_logic;
        enable   : in  std_logic;
        up_down  : in  std_logic;  -- '1' = up, '0' = down
        load     : in  std_logic;
        load_val : in  std_logic_vector(7 downto 0);
        count    : out std_logic_vector(7 downto 0);
        overflow : out std_logic
    );
end entity counter_8bit;

architecture behavioral of counter_8bit is
    signal cnt_reg : unsigned(7 downto 0) := (others => '0');
begin

    process(clk, rst)
    begin
        if rst = '1' then
            cnt_reg  <= (others => '0');
            overflow <= '0';
        elsif rising_edge(clk) then
            overflow <= '0';
            if load = '1' then
                cnt_reg <= unsigned(load_val);
            elsif enable = '1' then
                if up_down = '1' then
                    if cnt_reg = x"FF" then
                        overflow <= '1';
                    end if;
                    cnt_reg <= cnt_reg + 1;
                else
                    if cnt_reg = x"00" then
                        overflow <= '1';
                    end if;
                    cnt_reg <= cnt_reg - 1;
                end if;
            end if;
        end if;
    end process;

    count <= std_logic_vector(cnt_reg);

end architecture behavioral;
