// signal_filter.cpp -- Digital FIR filter implementation
// PEEKDOCS_TEST_MARKER

#include <vector>
#include <numeric>
#include <stdexcept>

class FIRFilter {
public:
    explicit FIRFilter(const std::vector<double>& coefficients)
        : coeffs_(coefficients), buffer_(coefficients.size(), 0.0), index_(0) {
        if (coefficients.empty()) {
            throw std::invalid_argument("Filter must have at least one coefficient");
        }
    }

    double process(double input) {
        buffer_[index_] = input;
        double output = 0.0;
        size_t j = index_;
        for (size_t i = 0; i < coeffs_.size(); ++i) {
            output += coeffs_[i] * buffer_[j];
            if (j == 0) j = coeffs_.size();
            --j;
        }
        index_ = (index_ + 1) % coeffs_.size();
        return output;
    }

    size_t order() const { return coeffs_.size() - 1; }

private:
    std::vector<double> coeffs_;
    std::vector<double> buffer_;
    size_t index_;
};
