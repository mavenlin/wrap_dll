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
cd wrap_dll
cmake CMakeLists.txt
```

### x86 DLL
```shell
python3 wrap_dll.py C:\Windows\SysWOW64\AudioSes.dll
cd wrap_dll
cmake CMakeLists.txt
```

## PS

This tool seems to be useful for some people, as I seem a few forks recently.
Therefore I performed a major refactor to make the code more professional.

Changes:
- Remove the `dumpbin.exe` included, the user can specify their own `dumpbin.exe` that comes with their visual studio installation. e.g. Mine is located at `C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.27.29110\bin\Hostx64\x64\dumpbin.exe`. The script by default assumes `dumpbin.exe` is available in the user's `PATH`.
- Use `cmake` to generate visual studio solution file.
- Use `jinja2` to separate the `c++/asm` code into independent template files.
- Support `--dry` flag to perform dry run, which only prints all the files to be generated.
