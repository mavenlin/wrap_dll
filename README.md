# Wrap DLL

A tool to automatically generate cpp/asm codes for wrapping a dynamic-link library.

## Features

- All the wrapper functions perform a `jmp` instruction that jumps to the real function.
- A CMake project is generated under the directory with the same name as the DLL.
- If the signature of any of the functions is known, the user can replace the default implementation with a custom function that performs API hooking / code injection.
- Both `x64` or `Win32` DLLs are supported.
- The original real DLL is prefixed with `real_` and copied to the project directory.

## Install

No installation is necessary, but you need `python>=3.7` to run it, and want to install the dependencies through

```shell
pip install -r requirements.txt
```

currently there's only `jinja2` for rendering the code templates.


## Example

### x64 DLL
```shell
python3 wrap_dll.py C:\Windows\System32\AudioSes.dll
cd AudioSes
cmake -f CMakeLists.txt
```

### x86 DLL
```shell
python3 wrap_dll.py C:\Windows\SysWOW64\AudioSes.dll
cd AudioSes
cmake -f CMakeLists.txt
```
### Override some of the exported functions
To override some of the functions, provide a `hook.h` file. 

Say if we wrap `abc_dll.dll` with the function `int abc(const char* a, int b, float c)`, override it in the `hook.h` with

```C++
/* 
 * content of file: hook.h
 */
#include "hook_macro.h"
/*
 * define a variable that is uppercase of the function name that you want to override.
 * which notifies the generated code that a override of the function is provided.
 */
#define ABC
/* 
 * Arguments of the FAKE macro is (return_type, call_convention, function_name, arg_type1 arg1, arg_type2 arg2, ...).
 */
FAKE(int, __cdecl, abc, const char* a, int b, float c) { // currently, the parsing code only support __cdecl functions.
  b = 0; // custom code before calling the real function.
  int ret = abc_real(a, b, c); // call the real function, FAKE macro prepares abc_real for you, which can be called directly.
  ret += 1; // custom code after calling the real function.
  return ret;
}
```

Now generate the wrapper with

```shell
python3 wrap_dll.py --hook hook.h abc_dll.dll
cd abc_dll
cmake -f CMakeLists.txt
```

## PS

This tool seems to be useful for some people, as I saw a few forks recently.
Therefore I performed a major refactor to make the code more professional.

Changes:
- Remove the `dumpbin.exe` included, the user can specify their own `dumpbin.exe` that comes with their visual studio installation. e.g. Mine is located at `C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.27.29110\bin\Hostx64\x64\dumpbin.exe`. The script by default assumes `dumpbin.exe` is available in the user's `PATH`.
- Use `cmake` to generate visual studio solution file.
- Use `jinja2` to separate the `c++/asm` code into independent template files.
- Support `--dry` flag to perform dry run, which only prints all the files to be generated.
