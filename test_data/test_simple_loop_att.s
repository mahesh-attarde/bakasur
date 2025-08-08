# AT&T Syntax test assembly with clear loops
	.text
	.globl	simple_loop_function_att
	.type	simple_loop_function_att, @function
simple_loop_function_att:
	pushq %rbp
	movq %rsp, %rbp
	movl $0, %eax
.loop_start:
	incl %eax
	cmpl $10, %eax
	jl .loop_start     # Back edge - should be red
	movl $0, %ecx
.inner_loop:
	incl %ecx
	cmpl $5, %ecx
	jl .inner_loop     # Back edge - should be red
	retq
.Lfunc_end0:
	.size	simple_loop_function_att, .Lfunc_end0-simple_loop_function_att
