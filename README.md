# Simplessembly
#### A simplified assembly experience

Assembly but the hard stuff is done for you.
Generates x86-64 Linux Nasm assembly

Generates Assembly, Assembles with Nasm, links with the GNU linker

Working on:
- Removing boilerplate assembly in labels jumped to by str_compare
- Better errors
- Control flow (wip)
- Interaction with the stack (push function) (wip)
- [Comparing strings](https://github.com/vstigial/Simplessembly/blob/main/tests/str_compare.txt) (wip)

  
# A Hello World 
### See [tests/hello_world.txt](https://github.com/vstigial/Simplessembly/blob/main/tests/hello_world.txt) for a walkthrough
```
use("std/std.txt");

global(_start);
begin_label(_start);

    str_var(db, string, "Hello, World!\n");
    write(string, 15);

    exit(0);
```
### This generates the required assembly code:
```assembly
SECTION .bss
SECTION .data
    string: db "Hello, World!", 0xD, 0xA, 0x0
SECTION .text
    global _start
_start:

    mov rax, 0x01
    mov rdi, 0x01
    mov rsi, string
    mov rdx, 15
    syscall

    mov rax, 0x3c
    mov rdi, 0
    syscall
```
### Which is then assembled and linked into an independent ELF64 executable
```shell
vstigial@Laptop$ file a.out
a.out: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), statically linked, not stripped
```
# Want to manually execute a syscall?
```
syscall(amount_of_arguments_you_want_passed,
        %rax register,
        %rdi register,  /* optional */
        %rsi register,  /* optional */
        %rdx register,  /* optional */
        %r10 register,  /* optional */
        %r8  register,  /* optional */
        %r9  register   /* optional */
       );
```
