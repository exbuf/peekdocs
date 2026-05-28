-- sample.vhdl -- VHDL testbench: verify PWM generator output
-- PEEKDOCS_TEST_MARKER

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity tb_pwm_generator is
end entity tb_pwm_generator;

architecture testbench of tb_pwm_generator is
    signal clk       : std_logic := '0';
    signal rst       : std_logic := '1';
    signal duty_cycle: std_logic_vector(7 downto 0) := x"80";
    signal pwm_out   : std_logic;

    constant CLK_PERIOD : time := 10 ns;  -- 100 MHz
begin

    -- Clock generation
    clk <= not clk after CLK_PERIOD / 2;

    -- Unit under test would be instantiated here
    -- uut: entity work.pwm_generator port map (...)

    stimulus: process
    begin
        -- Reset
        rst <= '1';
        wait for 100 ns;
        rst <= '0';

        -- Set 50% duty cycle
        duty_cycle <= x"80";
        wait for 10 us;

        -- Set 25% duty cycle
        duty_cycle <= x"40";
        wait for 10 us;

        -- Set 75% duty cycle
        duty_cycle <= x"C0";
        wait for 10 us;

        report "Testbench completed successfully" severity note;
        wait;
    end process stimulus;

end architecture testbench;
