# Simple test assembly with clear loops
	.text
	.globl	simple_loop_function
	.type	simple_loop_function, @function
simple_loop_function:
	push rbp
	mov rbp, rsp
	mov eax, 0
.loop_start:
	inc eax
	cmp eax, 10
	jl .loop_start     # Back edge - should be red
	mov ecx, 0
.inner_loop:
	inc ecx
	cmp ecx, 5
	jl .inner_loop     # Back edge - should be red
	ret
.Lfunc_end0:
	.size	simple_loop_function, .Lfunc_end0-simple_loop_function
