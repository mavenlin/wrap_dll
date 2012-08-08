.code
extern mProcs:QWORD
ExportByOrdinal1 proc
	jmp mProcs[0*8]
ExportByOrdinal1 endp
ExportByOrdinal2 proc
	jmp mProcs[1*8]
ExportByOrdinal2 endp
ExportByOrdinal3 proc
	jmp mProcs[2*8]
ExportByOrdinal3 endp
ExportByOrdinal4 proc
	jmp mProcs[3*8]
ExportByOrdinal4 endp
ExportByOrdinal5 proc
	jmp mProcs[4*8]
ExportByOrdinal5 endp
end
