# Simple RISC-V function that computes factorial
# Input: a0 (number)
# Output: a0 (factorial result)

factorial:
    # Base case: if n <= 1, return 1
    li t0, 1
    ble a0, t0, base_case
    
    # Save return address and argument
    addi sp, sp, -16
    sd ra, 8(sp)
    sd a0, 0(sp)
    
    # Recursive call: factorial(n-1)
    addi a0, a0, -1
    jal ra, factorial
    
    # Restore argument and multiply
    ld t1, 0(sp)
    mul a0, a0, t1
    
    # Restore return address and stack
    ld ra, 8(sp)
    addi sp, sp, 16
    ret

base_case:
    li a0, 1
    ret
