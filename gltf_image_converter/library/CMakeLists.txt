cmake_minimum_required(VERSION 3.22)

# workspace
project(texture-loader)

# Fix MSVC toolset toolset incompatibility
# Which causes crash for some users
add_compile_definitions(_DISABLE_CONSTEXPR_MUTEX_CONSTRUCTION)

# includes
include(FetchContent)

# install supercell-texture
FetchContent_Declare(
    supercell-texture
    GIT_REPOSITORY https://github.com/sc-workshop/SupercellTexture
    GIT_TAG main
)
FetchContent_MakeAvailable(supercell-texture)

# C++ headers and source files
file(GLOB_RECURSE HEADERS source/*.h)
file(GLOB_RECURSE SOURCES source/*.cpp source/*.hpp)

set(TARGET TextureLoader)

add_library(${TARGET} SHARED ${HEADERS} ${SOURCES})

wk_project_setup(${TARGET})

target_include_directories(${TARGET} PUBLIC source)

target_link_libraries(${TARGET} PRIVATE supercell::texture)