import os.path;
import sys;
import subprocess as sub
import re;
import shutil;
import time;

# Info
print ('Wrapper Generator. Copyright (C) Lin Min\n\n');

# Get the input parameter first.
dllname = sys.argv[1];

# Check whether is a dll file.
if not dllname.endswith('.dll'):
	print ('You should pass a dll file to this program!');
	sys.exit(1);

# Check whether the dll file specified exists.
if os.path.exists(dllname):
	print ('#############################')
	print ('Reading dll file ...');
else:
	print ('The Specified file \"'+dllname+'\" does not exist!');
	sys.exit(1);

# Check Architecture
architecture = 'Unknown';
p = sub.Popen('dumpbin_tools/dumpbin.exe /headers '+dllname,stdout=sub.PIPE,stderr=sub.PIPE);
output, errors = p.communicate();
output = output.decode('utf-8');
if 'x86' in output:
	print ('x86 dll detected ...');
	architecture = 'x86';
elif 'x64' in output:
	print ('x64 dll detected ...');
	architecture = 'x64';
else:
	print ('invalid dll file, exiting ...');
	
# Get Export List
p = sub.Popen('dumpbin_tools/dumpbin.exe /exports '+dllname,stdout=sub.PIPE,stderr=sub.PIPE);
output, errors = p.communicate();
output = output.decode('utf-8');
lines = output.split('\r\n');
start = 0; idx1 = 0; idx2 = 0; idx3 = 0; idx4 = 0; LoadNames = []; WrapFcn = []; DefItem = [];
for line in lines:
	if 'ordinal' in line and 'hint' in line and 'RVA' in line and 'name' in line:
		start = 1;
		idx1 = line.find('ordinal');
		idx2 = line.find('hint');
		idx3 = line.find('RVA');
		idx4 = line.find('name');
		continue;
	if start is 1:
		start = 2;
		continue;
	if start is 2:
		if len(line) is 0:
			break;
		splt = re.compile("\s*").split(line.strip());
		ordinal = splt[0];
		fcnname = splt[-1];
		if fcnname == '[NONAME]':
			LoadNames.append( '(LPCSTR)'+ordinal );
			WrapFcn.append('ExportByOrdinal'+ordinal);
			DefItem.append('ExportByOrdinal'+ordinal+' @'+ordinal+' NONAME');
		else:
			LoadNames.append( '\"'+fcnname+'\"' );
			WrapFcn.append(fcnname+'_wrapper');
			DefItem.append(fcnname+'='+fcnname+'_wrapper'+' @'+ordinal);
			
# Generate Def File
print ('Generating .def File');
f = open(dllname.replace('.dll','.def'),'w');
f.write('LIBRARY '+dllname+'\n');
f.write('EXPORTS\n');
for item in DefItem:
	f.write('\t'+item+'\n');
f.close();

# Generate CPP File
print ('Generating .cpp file');

f = open(dllname.replace('.dll','.cpp'),'w');
f.write('#include <windows.h>\n#include <stdio.h>\n');
f.write('HINSTANCE mHinst = 0, mHinstDLL = 0;\n');

if architecture == 'x64':  # For X64
	f.write('extern \"C\" ');

f.write('UINT_PTR mProcs['+str(len(LoadNames))+'] = {0};\n\n');
f.write('LPCSTR mImportNames[] = {');
for idx, val in enumerate(LoadNames):
	if idx is not 0:
		f.write(', ');
	f.write(val);
f.write('};\n');
f.write('BOOL WINAPI DllMain( HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved ) {\n');
f.write('\tmHinst = hinstDLL;\n');
f.write('\tif ( fdwReason == DLL_PROCESS_ATTACH ) {\n');
# f.write('\t\tchar sysdir[255], path[255];\n');
# f.write('\t\tGetSystemDirectory( sysdir, 254 );\n');
# f.write('\t\tsprintf( path, \"%s\\\\ori_'+dllname+'\", sysdir );\n');
f.write('\t\tmHinstDLL = LoadLibrary( \"ori_'+dllname+'\" );\n');
f.write('\t\tif ( !mHinstDLL )\n');
f.write('\t\t\treturn ( FALSE );\n');
f.write('\t\tfor ( int i = 0; i < '+str(len(LoadNames))+'; i++ )\n');
f.write('\t\t\tmProcs[ i ] = (UINT_PTR)GetProcAddress( mHinstDLL, mImportNames[ i ] );\n');
f.write('\t} else if ( fdwReason == DLL_PROCESS_DETACH ) {\n');
f.write('\t\tFreeLibrary( mHinstDLL );\n');
f.write('\t}\n');
f.write('\treturn ( TRUE );\n');
f.write('}\n\n');

if architecture == 'x64':
	for item in WrapFcn:
		f.write('extern \"C\" void '+item+'();\n');
else:
	for idx, item in enumerate(WrapFcn):
		f.write('extern \"C\" __declspec(naked) void __stdcall '+item+'(){__asm{jmp mProcs['+str(idx)+'*4]}}\n');
f.close();


# Generate ASM File
print ('Generating .asm file');
if architecture == 'x86':
	print ('x86 wrapper will use inline asm.');
else:
	f = open(dllname.replace('.dll','_asm.asm'),'w');
	f.write('.code\nextern mProcs:QWORD\n');
	for idx, item in enumerate(WrapFcn):
		f.write(item+' proc\n\tjmp mProcs['+str(idx)+'*8]\n'+item+' endp\n');
	f.write('end\n');
	f.close();
	
# Generate MS Visual Studio Project Files.

if os.path.exists(dllname.replace('.dll','')):
	shutil.rmtree(dllname.replace('.dll',''));
time.sleep(2);
os.mkdir(dllname.replace('.dll',''));
os.mkdir(dllname.replace('.dll','')+'\\'+dllname.replace('.dll',''));

# Generate x64
if architecture == 'x64':
	sln = open('Visual Studio Project Template\\x64\\MyName.sln','r');
	targetsln = open(dllname.replace('.dll','')+'\\'+dllname.replace('.dll','')+'.sln','w');
	for line in sln:
		line = line.replace('MyName',dllname.replace('.dll',''));
		line = line.replace('MYNAME',dllname.replace('.dll','').upper());
		targetsln.write(line);
	targetsln.close();
	sln.close();
	
	prj = open('Visual Studio Project Template\\x64\\MyName\\MyName.vcxproj','r');
	targetprj = open(dllname.replace('.dll','')+'\\'+dllname.replace('.dll','')+'\\'+dllname.replace('.dll','')+'.vcxproj','w');
	for line in prj:
		line = line.replace('MyName',dllname.replace('.dll',''));
		line = line.replace('MYNAME',dllname.replace('.dll','').upper());
		targetprj.write(line);
	targetprj.close();
	prj.close();
	
	prj = open('Visual Studio Project Template\\x64\\MyName\\MyName.vcxproj.filters','r');
	targetprj = open(dllname.replace('.dll','')+'\\'+dllname.replace('.dll','')+'\\'+dllname.replace('.dll','')+'.vcxproj.filters','w');
	for line in prj:
		line = line.replace('MyName',dllname.replace('.dll',''));
		line = line.replace('MYNAME',dllname.replace('.dll','').upper());
		targetprj.write(line);
	targetprj.close();
	prj.close();
	
	prj = open('Visual Studio Project Template\\x64\\MyName\\MyName.vcxproj.user','r');
	targetprj = open(dllname.replace('.dll','')+'\\'+dllname.replace('.dll','')+'\\'+dllname.replace('.dll','')+'.vcxproj.user','w');
	for line in prj:
		line = line.replace('MyName',dllname.replace('.dll',''));
		line = line.replace('MYNAME',dllname.replace('.dll','').upper());
		targetprj.write(line);
	targetprj.close();
	prj.close();
	
	shutil.copy('Visual Studio Project Template\\x64\\MyName.suo',dllname.replace('.dll','')+'\\'+dllname.replace('.dll','')+'.suo');
	
	shutil.move(dllname.replace('.dll','.cpp'),dllname.replace('.dll','')+'\\'+dllname.replace('.dll','')+'\\');
	shutil.move(dllname.replace('.dll','.def'),dllname.replace('.dll','')+'\\'+dllname.replace('.dll','')+'\\');
	shutil.move(dllname.replace('.dll','_asm.asm'),dllname.replace('.dll','')+'\\'+dllname.replace('.dll','')+'\\');

else:
	sln = open('Visual Studio Project Template\\x86\\MyName.sln','r');
	targetsln = open(dllname.replace('.dll','')+'\\'+dllname.replace('.dll','')+'.sln','w');
	for line in sln:
		line = line.replace('MyName',dllname.replace('.dll',''));
		line = line.replace('MYNAME',dllname.replace('.dll','').upper());
		targetsln.write(line);
	targetsln.close();
	sln.close();
	
	prj = open('Visual Studio Project Template\\x86\\MyName\\MyName.vcxproj','r');
	targetprj = open(dllname.replace('.dll','')+'\\'+dllname.replace('.dll','')+'\\'+dllname.replace('.dll','')+'.vcxproj','w');
	for line in prj:
		line = line.replace('MyName',dllname.replace('.dll',''));
		line = line.replace('MYNAME',dllname.replace('.dll','').upper());
		targetprj.write(line);
	targetprj.close();
	prj.close();
	
	prj = open('Visual Studio Project Template\\x86\\MyName\\MyName.vcxproj.filters','r');
	targetprj = open(dllname.replace('.dll','')+'\\'+dllname.replace('.dll','')+'\\'+dllname.replace('.dll','')+'.vcxproj.filters','w');
	for line in prj:
		line = line.replace('MyName',dllname.replace('.dll',''));
		line = line.replace('MYNAME',dllname.replace('.dll','').upper());
		targetprj.write(line);
	targetprj.close();
	prj.close();
	
	prj = open('Visual Studio Project Template\\x86\\MyName\\MyName.vcxproj.user','r');
	targetprj = open(dllname.replace('.dll','')+'\\'+dllname.replace('.dll','')+'\\'+dllname.replace('.dll','')+'.vcxproj.user','w');
	for line in prj:
		line = line.replace('MyName',dllname.replace('.dll',''));
		line = line.replace('MYNAME',dllname.replace('.dll','').upper());
		targetprj.write(line);
	targetprj.close();
	prj.close();
	
	shutil.copy('Visual Studio Project Template\\x86\\MyName.suo',dllname.replace('.dll','')+'\\'+dllname.replace('.dll','')+'.suo');
	
	shutil.move(dllname.replace('.dll','.cpp'),dllname.replace('.dll','')+'\\'+dllname.replace('.dll','')+'\\');
	shutil.move(dllname.replace('.dll','.def'),dllname.replace('.dll','')+'\\'+dllname.replace('.dll','')+'\\');
