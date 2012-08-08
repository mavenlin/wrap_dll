#include <windows.h>
#include <stdio.h>
HINSTANCE mHinst = 0, mHinstDLL = 0;
extern "C" UINT_PTR mProcs[5] = {0};

LPCSTR mImportNames[] = {(LPCSTR)1, (LPCSTR)2, (LPCSTR)3, (LPCSTR)4, (LPCSTR)5};
BOOL WINAPI DllMain( HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved ) {
	mHinst = hinstDLL;
	if ( fdwReason == DLL_PROCESS_ATTACH ) {
		char sysdir[255], path[255];
		GetSystemDirectory( sysdir, 254 );
		sprintf( path, "%s\\ori_depends.dll", sysdir );
		mHinstDLL = LoadLibrary( path );
		if ( !mHinstDLL )
			return ( FALSE );
		for ( int i = 0; i < 5; i++ )
			mProcs[ i ] = (UINT_PTR)GetProcAddress( mHinstDLL, mImportNames[ i ] );
	} else if ( fdwReason == DLL_PROCESS_DETACH ) {
		FreeLibrary( mHinstDLL );
	}
	return ( TRUE );
}

extern "C" void ExportByOrdinal1();
extern "C" void ExportByOrdinal2();
extern "C" void ExportByOrdinal3();
extern "C" void ExportByOrdinal4();
extern "C" void ExportByOrdinal5();
