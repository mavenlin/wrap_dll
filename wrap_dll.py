import os
import sys
import argparse
import subprocess
from jinja2 import Template

print("wrap_dll, Copyright 2020 Min Lin")

parser = argparse.ArgumentParser(description="make dll wrapper")
parser.add_argument("--dumpbin", type=str, default="dumpbin.exe",
                    help="The path to dumpbin.exe provided by visual studio")
parser.add_argument("dll", type=str, help="The path to the dll file to wrap")
args = parser.parse_args()

def architecture(dumpbin, dll):
  output = subprocess.check_output([
      dumpbin, "/HEADERS", dll
  ])
  # inspect the output
  if not "File Type: DLL" in output:
    raise RuntimeError(f"{dll} is not a DLL file")
  if "x86" in output:
    print("x86 DLL detected")
    arch = "x86"
  elif "x64" in output:
    print("x64 DLL detected")
    arch = "x64";
  else:
    raise RuntimeError(f"{dll} is not a valid DLL file")
  return arch

def extract_symbols(dumpbin, dll):
  output = subprocess.check_output([
      dumpbin, "/EXPORTS", dll
  ])
  lines = output.split("\r\n")
  start, end = None, None
  start = next(idx for idx, line in enumerate(lines)
               if all(map(lambda entry: (entry in line),
                          ["ordinal", "hint", "RVA", "name"]))) + 2
  end = next(idx for idx, line in enumerate(lines) if line == "")
  lines = lines[start:end]
  ordinal_name_pairs = []
  for line in lines:
    if "(forwarded" in line:
      ordinal, hint, name, *others = line.split()
    else:
      ordinal, hint, RVA, name = line.split()
    ordinal_name_pairs.append((ordinal, name))
  return ordinal_name_pairs

if __name__ == "__main__":
  if not os.path.isfile(args.dumpbin):
    raise RuntimeError("dumpbin.exe not found in PATH, "
                       "maybe specify its path through the --dumpbin argument?")
  if not os.path.isfile(args.dll):
    raise RuntimeError(f"{args.dll} is not a valid file")

  with open("def_template") as def_template_file:
    def_template = Template(def_template_file.read(), trim_blocks=True,
                            lstrip_blocks=True)

  with open("cpp_template") as cpp_template_file:
    cpp_template = Template(cpp_template_file.read(), trim_blocks=True,
                            lstrip_blocks=True)

  with open("asm_template") as asm_template_file:
    asm_template = Template(asm_template_file.read(), trim_blocks=True,
                            lstrip_blocks=True)

  with open("cmake_template") as cmake_template_file:
    cmake_template = Template(cmake_template_file.read(), trim_blocks=True,
                              lstrip_blocks=True)

  arch = architecture(args.dumpbin, args.dll)
  ordinal_name_pairs = extract_symbols(args.dumpbin, args.dll)
  def_content = def_template.render(ordinal_name_pairs=ordinal_name_pairs)
  cpp_content = cpp_template.render(dll=args.dll, architecture=arch,
                                    ordinal_name_pairs=ordinal_name_pairs)
  asm_content = asm_template.render(ordinal_name_pairs=ordinal_name_pairs)
  cmake_content = cmake_template.render(dll=args.dll)
