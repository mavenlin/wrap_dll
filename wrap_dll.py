import os
import sys
import shutil
import argparse
import subprocess
from jinja2 import Template

parser = argparse.ArgumentParser(description="make dll wrapper")
parser.add_argument("--dumpbin", type=str, default="dumpbin.exe",
                    help="The path to dumpbin.exe provided by visual studio")
parser.add_argument("--undname", type=str, default="undname.exe",
                    help="The path to undname.exe provided by visual studio")
parser.add_argument("--dry", action='store_true', help="Dry run")
parser.add_argument("--force", action='store_true',
                    help="WARNING: force regeneration will delete old files")
parser.add_argument("--hook", type=str, default="", help="Define fake functions")
parser.add_argument("dll", type=str, help="The path to the dll file to wrap")
args = parser.parse_args()

def architecture(dll):
  if not (dll.endswith(".dll") or dll.endswith(".DLL")):
    raise RuntimeError(f"{dll} needs to have .dll extension")
  output = subprocess.check_output([
      args.dumpbin, "/HEADERS", dll
  ])
  output = output.decode("utf-8")
  # inspect the output
  if not "File Type: DLL" in output:
    raise RuntimeError(f"{dll} is not a DLL file")
  if "x86" in output:
    print(f"{dll} is a x86 DLL")
    arch = "x86"
  elif "x64" in output:
    print(f"{dll} is a x64 DLL")
    arch = "x64";
  else:
    raise RuntimeError(f"{dll} is not a valid DLL file")
  return arch

def extract_symbols(dll):
  output = subprocess.check_output([
      args.dumpbin, "/EXPORTS", dll
  ])
  output = output.decode("utf-8")
  lines = output.split("\r\n")
  start, end = None, None
  start = next(idx for idx, line in enumerate(lines)
               if all(map(lambda entry: (entry in line),
                          ["ordinal", "hint", "RVA", "name"]))) + 2
  lines = lines[start:]
  end = next(idx for idx, line in enumerate(lines) if line == "")
  lines = lines[:end]
  if len(lines) == 0:
    raise RuntimeError(f"No exported symbols for {dll}")
  ordinal_name_pairs = []
  for line in lines:
    if "(forwarded" in line:
      ordinal, hint, name, *others = line.split()
    elif "[NONAME]" in line:
      ordinal, RVA, name, *others = line.split()
    else:
      ordinal, hint, RVA, name, *others = line.split()
    ordinal_name_pairs.append((ordinal, name))
  return ordinal_name_pairs

def undecorate(names):
  import tempfile
  with tempfile.NamedTemporaryFile(mode='w+t') as f:
    f.write("\n".join(names))
    f.flush()
    demangled = subprocess.check_output([
        args.undname, f.name
    ])
  demangled = demangled.decode("utf-8")
  demangled = demangled.split("\r\n")
  undecorated = []
  for index, (dname, name) in enumerate(zip(demangled, names)):
    if dname == name: # C function
      dname.replace("@", "_") # remove __stdcall, __fastcall decorations
    else:
      end_index = dname.find("(")
      start_index = dname[:end_index].rfind(" ")
      dname = dname[start_index:end_index].replace("::", "_").strip()
      dname = f"CXX_FN_{index}_{dname}"
    undecorated.append(dname)
  return undecorated

def write_file(filename, content):
  if args.dry:
    print(f"-------- {filename} --------")
    print(content)
    print(f"\n")
    return
  else:
    with open(filename, "w") as f:
      f.write(content)

if __name__ == "__main__":
  if shutil.which(args.dumpbin) is None:
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

  dll = os.path.basename(args.dll)
  dll_name = dll[:-4]
  arch = architecture(args.dll)
  ordinal_name_pairs = extract_symbols(args.dll)
  ordinals = [ordinal for ordinal, _ in ordinal_name_pairs]
  names = [name for _, name in ordinal_name_pairs]
  undecorated_names = undecorate(names)
  ordinal_and_names = list(zip(ordinals, names, undecorated_names))

  if not args.dry:
    if args.force:
      if os.path.exists(dll_name):
        shutil.rmtree(dll_name)
    os.makedirs(dll_name)
    shutil.copy(args.dll, f"{dll_name}/real_{dll}")
    if args.hook != "":
      shutil.copy(args.hook, f"{dll_name}/")
    else:
      args.hook = "empty.h"
      from pathlib import Path
      Path(f"{dll_name}/empty.h").touch()
    shutil.copy("hook_macro.h", f"{dll_name}/")

  # write files
  def_content = def_template.render(ordinal_and_names=ordinal_and_names)
  write_file(f"{dll_name}/{dll_name}.def", def_content)

  cpp_content = cpp_template.render(dll=dll, architecture=arch, hook=args.hook,
                                    ordinal_and_names=ordinal_and_names)
  write_file(f"{dll_name}/{dll_name}.cpp", cpp_content)

  cmake_content = cmake_template.render(
      dll=dll_name, architecture=arch, hook=args.hook)
  write_file(f"{dll_name}/CMakeLists.txt", cmake_content)

  if arch == "x64":
    asm_content = asm_template.render(ordinal_and_names=ordinal_and_names)
    write_file(f"{dll_name}/{dll_name}_asm.asm", asm_content)
