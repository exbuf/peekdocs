# unit_converter.rb -- Engineering unit conversion library
# PEEKDOCS_TEST_MARKER

class UnitConverter
  CONVERSIONS = {
    temperature: {
      celsius_to_fahrenheit: ->(c) { c * 9.0 / 5.0 + 32.0 },
      fahrenheit_to_celsius: ->(f) { (f - 32.0) * 5.0 / 9.0 },
      celsius_to_kelvin:     ->(c) { c + 273.15 },
      kelvin_to_celsius:     ->(k) { k - 273.15 }
    },
    pressure: {
      psi_to_bar:  ->(psi) { psi * 0.0689476 },
      bar_to_psi:  ->(bar) { bar / 0.0689476 },
      psi_to_kpa:  ->(psi) { psi * 6.89476 },
      atm_to_psi:  ->(atm) { atm * 14.696 }
    }
  }.freeze

  def self.convert(category, conversion, value)
    fn = CONVERSIONS.dig(category, conversion)
    raise ArgumentError, "Unknown conversion: #{category}/#{conversion}" unless fn
    fn.call(value)
  end

  def self.available_conversions
    CONVERSIONS.flat_map { |cat, convs| convs.keys.map { |k| "#{cat}/#{k}" } }
  end
end
