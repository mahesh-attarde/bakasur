# Create a simple assembly file that works with our existing parser
# This is a subset of the MonteCarlo_integrate function for demonstration
	.intel_syntax noprefix
	.text
	.globl	MonteCarlo_integrate
	.type	MonteCarlo_integrate, @function
MonteCarlo_integrate:
	push rbp
	push r15
	push r14
	push r13
	push r12
	push rbx
	sub rsp, 232
	mov eax, dword ptr [rdi + 284]
	test eax, eax
	jle .LBB0_47
.LBB0_3:
	mov r14, rdi
	xor ebx, ebx
	cmp al, 32
	jne .LBB0_54
.LBB0_6:
	mov dword ptr [rsp + 16], edx
	call random_u32
	mov edx, eax
	and edx, 4095
	cmp qword ptr [rsp + 72], rdx
	jb .LBB0_10
.LBB0_9:
	lea esi, [rax + rdx]
	and esi, 4095
	vmovss xmm0, dword ptr [rcx + 4*rsi]
	vmovss dword ptr [r14 + 4*rdx], xmm0
	inc rdx
	cmp r12, rdx
	jne .LBB0_9
	jmp .LBB0_21
.LBB0_10:
	test rbp, rbp
	je .LBB0_16
.LBB0_13:
	lea esi, [rdx + rax]
	vmovd xmm0, esi
	add rdx, 8
	cmp rdx, rdi
	jne .LBB0_13
	jmp .LBB0_21
.LBB0_16:
	xor edx, edx
	jmp .LBB0_20
.LBB0_20:
	lea esi, [rax + rdx]
	and esi, 4095
	vmovss xmm0, dword ptr [rcx + 4*rsi]
	vmovss dword ptr [r14 + 4*rdx], xmm0
	inc rdx
	cmp r12, rdx
	jne .LBB0_20
.LBB0_21:
	call random_u32
	mov rdx, qword ptr [rsp + 32]
	add edx, eax
	and edx, 4095
	lea rdx, [rcx + 4*rdx]
	cmp rdx, r15
	jb .LBB0_25
.LBB0_24:
	lea esi, [rax + rdx]
	and esi, 4095
	vmovss xmm0, dword ptr [rcx + 4*rsi]
	vmovss dword ptr [r15 + 4*rdx], xmm0
	inc rdx
	cmp r12, rdx
	jne .LBB0_24
	jmp .LBB0_36
.LBB0_25:
	test rbp, rbp
	je .LBB0_31
.LBB0_28:
	lea esi, [rdx + rax]
	vmovd xmm0, esi
	add rdx, 8
	cmp rdx, rdi
	jne .LBB0_28
	jmp .LBB0_36
.LBB0_31:
	xor edx, edx
	jmp .LBB0_35
.LBB0_35:
	lea esi, [rax + rdx]
	and esi, 4095
	vmovss xmm0, dword ptr [rcx + 4*rsi]
	vmovss dword ptr [r15 + 4*rdx], xmm0
	inc rdx
	cmp r12, rdx
	jne .LBB0_35
.LBB0_36:
	vmovq rax, xmm6
	test rax, rax
	je .LBB0_41
.LBB0_39:
	vmovups ymm2, ymmword ptr [r14 + 4*rax]
	vmulps ymm2, ymm2, ymm2
	add rax, 8
	cmp rax, rdi
	jne .LBB0_39
	jmp .LBB0_45
.LBB0_41:
	xor eax, eax
	vmovss xmm2, dword ptr [rip + .LCPI0_4]
	mov edx, dword ptr [rsp + 16]
	jmp .LBB0_46
.LBB0_45:
	vpshufd xmm1, xmm0, 238
	vpaddd xmm0, xmm0, xmm1
	add ebx, ecx
	jmp .LBB0_5
.LBB0_5:
	inc edx
	cmp edx, dword ptr [rsp + 12]
	je .LBB0_93
	jmp .LBB0_6
.LBB0_46:
	vmovss xmm0, dword ptr [r14 + 4*rax]
	vmovss xmm1, dword ptr [r15 + 4*rax]
	vmulss xmm0, xmm0, xmm0
	inc rax
	cmp r12, rax
	jne .LBB0_46
	jmp .LBB0_5
.LBB0_47:
	cmp dword ptr [rsp + 12], 8
	jb .LBB0_50
.LBB0_50:
	mov ebx, dword ptr [rsp + 12]
	mov eax, ebx
	and eax, 2147483640
	sub ebx, eax
	je .LBB0_51
.LBB0_52:
	mov rdi, qword ptr [r14 + 376]
	call random_u32
	dec ebx
	jne .LBB0_52
.LBB0_51:
	vxorps xmm1, xmm1, xmm1
	jmp .LBB0_94
.LBB0_54:
	xor edx, edx
	jmp .LBB0_56
.LBB0_55:
	inc edx
	cmp edx, dword ptr [rsp + 12]
	je .LBB0_93
.LBB0_56:
	mov dword ptr [rsp + 16], edx
	call random_u32
	mov rdx, qword ptr [rsp + 32]
	add edx, eax
	and edx, 4095
	lea rdx, [rcx + 4*rdx]
	cmp qword ptr [rsp + 72], rdx
	jb .LBB0_60
.LBB0_59:
	lea esi, [rax + rdx]
	and esi, 4095
	vmovss xmm0, dword ptr [rcx + 4*rsi]
	vmovss dword ptr [r14 + 4*rdx], xmm0
	inc rdx
	cmp r12, rdx
	jne .LBB0_59
	jmp .LBB0_69
.LBB0_60:
	test rbp, rbp
	je .LBB0_67
.LBB0_62:
	lea esi, [rdx + rax]
	and esi, 4095
	vmovss xmm0, dword ptr [rcx + 4*rsi]
	add rdx, 4
	cmp rdx, rdi
	jne .LBB0_62
	jmp .LBB0_69
.LBB0_67:
	xor esi, esi
	jmp .LBB0_68
.LBB0_68:
	lea edx, [rax + rsi]
	and edx, 4095
	vmovss xmm0, dword ptr [rcx + 4*rdx]
	vmovss dword ptr [r14 + 4*rsi], xmm0
	inc rsi
	cmp r12, rsi
	jne .LBB0_68
.LBB0_69:
	call random_u32
	mov rdx, qword ptr [rsp + 32]
	add edx, eax
	and edx, 4095
	lea rdx, [rcx + 4*rdx]
	cmp rdx, r15
	jb .LBB0_73
.LBB0_72:
	lea esi, [rax + rdx]
	and esi, 4095
	vmovss xmm0, dword ptr [rcx + 4*rsi]
	vmovss dword ptr [r15 + 4*rdx], xmm0
	inc rdx
	cmp r12, rdx
	jne .LBB0_72
	jmp .LBB0_82
.LBB0_73:
	test rbp, rbp
	je .LBB0_80
.LBB0_75:
	lea esi, [rdx + rax]
	and esi, 4095
	vmovss xmm0, dword ptr [rcx + 4*rsi]
	add rdx, 4
	cmp rdx, r10
	jne .LBB0_75
	jmp .LBB0_82
.LBB0_80:
	xor esi, esi
	jmp .LBB0_81
.LBB0_81:
	lea edx, [rax + rsi]
	and edx, 4095
	vmovss xmm0, dword ptr [rcx + 4*rdx]
	vmovss dword ptr [r15 + 4*rsi], xmm0
	inc rsi
	cmp r12, rsi
	jne .LBB0_81
.LBB0_82:
	vmovq rax, xmm6
	test rax, rax
	je .LBB0_87
.LBB0_85:
	vmovups ymm2, ymmword ptr [r14 + 4*rax]
	vmulps ymm2, ymm2, ymm2
	add rax, 8
	cmp rax, r10
	jne .LBB0_85
	jmp .LBB0_91
.LBB0_87:
	xor eax, eax
	vmovss xmm3, dword ptr [rip + .LCPI0_6]
	mov edx, dword ptr [rsp + 16]
	jmp .LBB0_92
.LBB0_91:
	vpshufd xmm1, xmm0, 238
	vpaddd xmm0, xmm0, xmm1
	add ebx, ecx
	jne .LBB0_55
.LBB0_92:
	vmovss xmm0, dword ptr [r14 + 4*rax]
	vmovss xmm1, dword ptr [r15 + 4*rax]
	vmulss xmm0, xmm0, xmm0
	inc rax
	cmp r12, rax
	jne .LBB0_92
	jmp .LBB0_55
.LBB0_93:
	vcvtsi2ss xmm0, xmm15, ebx
	vmulss xmm1, xmm0, dword ptr [rip + .LCPI0_7]
.LBB0_94:
	vcvtsi2ss xmm0, xmm15, dword ptr [rsp + 12]
	vdivss xmm0, xmm1, xmm0
	add rsp, 232
	pop rbx
	pop r12
	pop r13
	pop r14
	pop r15
	pop rbp
	ret
.Lfunc_end0:
	.size	MonteCarlo_integrate, .Lfunc_end0-MonteCarlo_integrate
