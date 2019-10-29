DLL Wrapper Generator
=====================

Automatic generation of Dll wrapper for both 32 bit and 64 bit Dll.

This code parses a windows DLL and generates a wrapper that exports the same symbol. 
By default, the wrapper function points to the original function by a jump instruction.
You can modify and insert code for some of the function if you know the its signature.

PS: I wrote it quite a long time ago, but now I don't have time to update it.
I also don't have a windows machine to test any pull requests sent to me. Please feel free to fork.
