// matrix_math.hpp -- Lightweight 4x4 matrix class for 3D transforms
// PEEKDOCS_TEST_MARKER

#ifndef MATRIX_MATH_HPP
#define MATRIX_MATH_HPP

#include <array>
#include <cmath>

class Matrix4x4 {
public:
    Matrix4x4() : data_{} { for (int i = 0; i < 4; ++i) data_[i][i] = 1.0; }

    double& operator()(int row, int col) { return data_[row][col]; }
    double  operator()(int row, int col) const { return data_[row][col]; }

    Matrix4x4 operator*(const Matrix4x4& rhs) const {
        Matrix4x4 result;
        for (int i = 0; i < 4; ++i)
            for (int j = 0; j < 4; ++j) {
                result.data_[i][j] = 0.0;
                for (int k = 0; k < 4; ++k)
                    result.data_[i][j] += data_[i][k] * rhs.data_[k][j];
            }
        return result;
    }

    static Matrix4x4 rotation_z(double radians) {
        Matrix4x4 m;
        m.data_[0][0] =  std::cos(radians);
        m.data_[0][1] = -std::sin(radians);
        m.data_[1][0] =  std::sin(radians);
        m.data_[1][1] =  std::cos(radians);
        return m;
    }

private:
    double data_[4][4];
};

#endif // MATRIX_MATH_HPP
