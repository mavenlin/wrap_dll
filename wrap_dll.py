import os
import sys
import shutil
import argparse
import subprocess
from jinja2 import Template

parser = argparse.ArgumentParser(description="make dll wrapper")
parser.add_argument("--dumpbin", type=str, default="dumpbin.exe",
                    help="The path to dumpbin.exe provided by visual studio")
parser.add_argument("--dry", action='store_true', help="Dry run")
parser.add_argument("--force", action='store_true',
                    help="WARNING: force regeneration will delete old files")
parser.add_argument("dll", type=str, help="The path to the dll file to wrap")
args = parser.parse_args()

def architecture(dumpbin, dll):
  if not (dll.endswith(".dll") or dll.endswith(".DLL")):
    raise RuntimeError(f"{dll} needs to have .dll extension")
  output = subprocess.check_output([
      dumpbin, "/HEADERS", dll
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

def extract_symbols(dumpbin, dll):
  output = subprocess.check_output([
      dumpbin, "/EXPORTS", dll
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
  arch = architecture(args.dumpbin, args.dll)
  ordinal_name_pairs = extract_symbols(args.dumpbin, args.dll)

  if not args.dry:
    if args.force:
      if os.path.exists(dll_name):
        shutil.rmtree(dll_name)
    os.makedirs(dll_name)
    shutil.copy(args.dll, f"{dll_name}/real_{dll}")

  # write files
  def_content = def_template.render(ordinal_name_pairs=ordinal_name_pairs)
  write_file(f"{dll_name}/{dll_name}.def", def_content)

  cpp_content = cpp_template.render(dll=dll, architecture=arch,
                                    ordinal_name_pairs=ordinal_name_pairs)
  write_file(f"{dll_name}/{dll_name}.cpp", cpp_content)

  cmake_content = cmake_template.render(dll=dll_name, architecture=arch)
  write_file(f"{dll_name}/CMakeLists.txt", cmake_content)

  if arch == "x64":
    asm_content = asm_template.render(ordinal_name_pairs=ordinal_name_pairs)
    write_file(f"{dll_name}/{dll_name}_asm.asm", asm_content)
