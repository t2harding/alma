Steps to build code
```bash
mkdir build
cd build
cmake -DSTM32_CHIP=STM32L152RE -DCMAKE_TOOLCHAIN_FILE=~/src/stm32-cmake/cmake/gcc_stm32.cmake -DTOOLCHAIN_PREFIX=/usr/local/gcc-arm-none-eabi-6_2-2016q4/ -DSTM32Cube_DIR=~/tools/stm32_cube/STM32Cube_FW_L1_V1.7.0 ../
make
```
