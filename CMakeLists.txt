cmake_minimum_required(VERSION 3.18)

project(pycork VERSION 0.1.3 LANGUAGES C CXX)

# =========================================================
# C++ STANDARD
# =========================================================
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# =========================================================
# OPTIONS (minimal, no platform logic)
# =========================================================
option(BUILD_PYTHON "Build Python module" ON)
option(BUILD_STATIC "Build static cork library" OFF)

# =========================================================
# DEPENDENCY BASE
# =========================================================
include(GNUInstallDirs)
find_package(PkgConfig QUIET)

# =========================================================
# GMP (bulletproof)
# =========================================================
if(PkgConfig_FOUND)
    pkg_check_modules(GMP QUIET gmp)
endif()

if(NOT GMP_FOUND OR NOT GMP_LIBRARIES)
    find_path(GMP_INCLUDE_DIR gmp.h)
    find_library(GMP_LIBRARY gmp)

    if(GMP_INCLUDE_DIR AND GMP_LIBRARY)
        set(GMP_INCLUDE_DIRS ${GMP_INCLUDE_DIR})
        set(GMP_LIBRARIES ${GMP_LIBRARY})
    else()
        message(FATAL_ERROR "GMP not found (install libgmp-dev / gmp / vcpkg)")
    endif()
endif()

# =========================================================
# Eigen (header-only)
# =========================================================
find_path(EIGEN_INCLUDE_DIR
    NAMES Eigen/Core
    PATHS /usr/include/eigen3 /usr/local/include/eigen3
)

if(NOT EIGEN_INCLUDE_DIR)
    message(FATAL_ERROR "Eigen not found (install libeigen3-dev)")
endif()

# =========================================================
# fmt (hybrid: system or header-only fallback)
# =========================================================
find_package(fmt CONFIG QUIET)

if(NOT fmt_FOUND)
    find_path(FMT_INCLUDE_DIR fmt/core.h
        PATHS external/fmt/include /usr/include /usr/local/include
    )

    if(NOT FMT_INCLUDE_DIR)
        message(FATAL_ERROR "fmt not found")
    endif()
endif()

# =========================================================
# filesystem (vendored)
# =========================================================
set(FILESYSTEM_INCLUDE_DIR ${CMAKE_SOURCE_DIR}/external/filesystem)

# =========================================================
# pybind11
# =========================================================
add_subdirectory(external/pybind11)

find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)

# =========================================================
# GLOBAL DEFINES (cleaned)
# =========================================================
# CORK_DEBUG 
add_compile_definitions(
    PROJECT_VERSION=\"${PROJECT_VERSION}\"
    NOMINMAX
    FMT_HEADER_ONLY
    _USE_MATH_DEFINES
    ANSI_DECLARATORS
    TRIANGLE_INTEL64
    REDUCED
    CDT_ONLY   
    ANSI_DECLARATORS 
    _USE_MATH_DEFINES
    TRILIBRARY
    NO_TIMER 
    _CRT_SECURE_NO_WARNINGS
)

# =========================================================
# CORE SOURCES
# =========================================================
set(CORK_SOURCES
    cork/cork.h
    cork/accel/aabvh.h
    cork/file_formats/files.h
    cork/isct/absext4.h
    cork/isct/empty3d.h
    cork/isct/ext4.h
    cork/isct/fixext4.h
    cork/isct/fixint.h
    cork/isct/gmpext4.h
    cork/isct/quantization.h
    cork/isct/triangle.h
    cork/isct/unsafeRayTriIsct.h
    cork/math/bbox.h
    cork/math/ray.h
    cork/math/vec.h
    cork/mesh/mesh.h
    cork/rawmesh/rawMesh.h
    cork/util/iterPool.h
    cork/util/memPool.h
    cork/util/prelude.h
    cork/util/shortVec.h
    cork/util/unionFind.h
    cork/mesh/mesh.remesh.tpp
    cork/mesh/mesh.isct.tpp
    cork/mesh/mesh.bool.tpp
    cork/mesh/mesh.cpp

    cork/cork.cpp
    cork/file_formats/files.cpp
    cork/file_formats/ifs.cpp
    cork/file_formats/off.cpp
    cork/isct/empty3d.cpp
    cork/isct/quantization.cpp
    cork/isct/triangle.cpp
    cork/util/log.cpp
    cork/util/timer.cpp
)

# =========================================================
# STATIC CORE LIB
# =========================================================
add_library(cork_static STATIC ${CORK_SOURCES})

target_include_directories(cork_static PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_BINARY_DIR}
    ${GMP_INCLUDE_DIRS}
    ${EIGEN_INCLUDE_DIR}
    ${FMT_INCLUDE_DIR}
    ${FILESYSTEM_INCLUDE_DIR}
)

target_link_libraries(cork_static PRIVATE
    ${GMP_LIBRARIES}
)

# =========================================================
# EXPORT HEADER (required, kept clean)
# =========================================================
include(GenerateExportHeader)

generate_export_header(cork_static
    BASE_NAME cork
    EXPORT_MACRO_NAME CORK_EXPORT
    EXPORT_FILE_NAME CORK_Export.h
    STATIC_DEFINE CORK_STATIC_BUILD
)

target_include_directories(cork_static PUBLIC
    ${CMAKE_CURRENT_BINARY_DIR}
)

# =========================================================
# PYTHON MODULE
# =========================================================
if(BUILD_PYTHON)

    message(STATUS "Building pycork Python module")

    set(PYCORK_SOURCES
        python/pycork/module.cpp
    )

    pybind11_add_module(pycork MODULE ${PYCORK_SOURCES})

    target_link_libraries(pycork PRIVATE
        pybind11::module
        cork_static
        ${GMP_LIBRARIES}
    )

    set_target_properties(pycork PROPERTIES
        PREFIX ""
        SUFFIX "${Python3_EXTENSION_MODULE_SUFFIX}"
        CXX_VISIBILITY_PRESET hidden
        VISIBILITY_INLINES_HIDDEN ON
    )

    install(TARGETS pycork
        LIBRARY DESTINATION pycork
        RUNTIME DESTINATION pycork
    )

endif()

# =========================================================
# CLI TOOL (optional)
# =========================================================
add_executable(main cork/main.cpp)

target_link_libraries(main PRIVATE
    cork_static
    ${GMP_LIBRARIES}
)