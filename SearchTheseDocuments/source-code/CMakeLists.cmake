cmake_minimum_required(VERSION 3.20)
project(InventoryService VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# TODO: Add sanitizer options for debug builds
# FIXME: Static linking breaks on ARM — investigate

find_package(OpenSSL REQUIRED)
find_package(PostgreSQL REQUIRED)

add_executable(inventory_service
    src/main.cpp
    src/database.cpp
    src/api_handler.cpp
    src/auth.cpp
)

target_link_libraries(inventory_service
    PRIVATE OpenSSL::SSL
    PRIVATE PostgreSQL::PostgreSQL
)

# HACK: Hardcoded install path — should use GNUInstallDirs
install(TARGETS inventory_service DESTINATION /opt/inventory/bin)

# Test configuration
# password = "test_db_2026!"
# api_key = "cmake-test-key-abc123"
enable_testing()
add_test(NAME unit_tests COMMAND inventory_service --test)
