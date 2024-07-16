import sys
import os
import re

def split_ignore_quotes(args):
    pattern = re.compile(r'''((?:[^,"']|"[^"]*"|'[^']*')+)''')
    args_list = pattern.findall(args)
    args_list = [piece.strip('"\'') for piece in args_list]
    return args_list

out = open("out.asm", 'w')
out.close()

out = []
dat_num = 0
bss_num = 0
line_num = 0
out.insert(line_num, "SECTION .bss\n")
out.insert(line_num+1, "") # data section to avoid problems with list comprehension
out.insert(line_num+2, "SECTION .data\n")
out.insert(line_num+3, "")
out.insert(line_num+4, "SECTION .text\n")
out.insert(line_num+5, "")
# out.insert(line_num+3, "    global _start\n")
# out.insert(line_num+4, "_start:\n")
line_num += 6

file = open(sys.argv[1], 'r')
file = file.read()

pattern = re.compile(r'''((?:[^;"']|"[^"]*"|'[^']*')+)''')
file = pattern.findall(file)
lines = [piece.strip('"\'') for piece in file]

# lines = file.split(';') # add support for usage of these in strings later
cur_pos = -1 # 0 indexing

for line in lines:
    line = line.strip()
    cur_pos +=1
    if line:
        if "(" not in line and ")" not in line:
            print("Error: Malformed function call p1: " + str(line))
            sys.exit(1)

        function_name, args = line.strip().split("(", 1)
        function_name = function_name.strip()

        if args.endswith(")"):
            args = args[:-1]
        else:
            print("Error: Malformed function call p2: " + str(line))
            sys.exit(1)
        args_list = split_ignore_quotes(args)

    else:
        continue

    if function_name == "comment": # make better comment system
        pass                       # this is stupid

    elif function_name == "raw_asm":
        out.insert(line_num, f"{args_list[0][1:]}") # 1:-1 for quotes
        line_num += 1

    elif function_name == "reserve":
        out.insert(2, out[1] + f"    {args_list[2].strip()} {args_list[0].strip()} {args_list[1].strip()}\n")
        bss_num += 1
        line_num += 1

    elif function_name == "str_var":
        if '\\n' in args_list[2]:
            split_res = args_list[2].strip().split('\\n')
            increment = 0
            split_res[increment] = f"{args_list[0].strip()} {split_res[increment].strip()}\", 0xD, 0xA\n"
            increment += 1
            if args_list[2].strip().count("\\n") > 1:
                for newline in split_res:
                    split_res[increment] = f"    {args_list[0].strip()} \"{split_res[increment].strip()}\", 0xD, 0xA\n"
                    increment += 1
                    if increment == args_list[2].strip().count("\\n"):
                        break;
            split_res[increment] = f"    {args_list[0].strip()} \"{split_res[increment].strip()}\", 0x0\n"
            args_list[2] = ''.join(split_res)
            out.insert(4+bss_num, out[3+bss_num] + f"    {args_list[1]}: {args_list[2]}\n")

        else:
            out.insert(4+bss_num, out[3+bss_num] + f"    {args_list[1].strip()}: {args_list[0].strip()} {args_list[2]}, 0x0\n")
            args_list[2] = args_list[2] + '"'
        dat_num += 1
        line_num += 1

    elif function_name == "int_var":
        out.insert(4+bss_num, out[3+bss_num] + f"    {args_list[1].strip()} {args_list[0].strip()} {args_list[2]}\n")
        dat_num += 1
        line_num += 1

    elif function_name == "exit":
        out.insert(line_num, "    mov rax, 60\n")
        out.insert(line_num+1, f"    mov rdi, {args_list[0].strip()}\n")
        out.insert(line_num+2, "    syscall\n")
        line_num += 3

    elif function_name == "push":
        out.insert(line_num, f"    push {args_list[0]}\n")
        line_num += 1

    elif function_name == "move":
        out.insert(line_num, f"    mov {args_list[0].strip()}, {args_list[1]}\n")
        line_num += 1

    elif function_name == "compare":
        out.insert(line_num, f"    cmp {args_list[0].strip()}, {args_list[1]}\n")
        line_num += 1

    elif function_name == "j_equal":
        out.insert(line_num, f"    je {args_list[0].strip()}\n")
        line_num += 1

    elif function_name == "j_nequal":
        out.insert(line_num, f"    jne {args_list[0].strip()}\n")
        line_num += 1

    elif function_name == "write":
        out.insert(line_num, "    mov rax, 1\n")
        out.insert(line_num+1, "    mov rdi, 1\n")
        out.insert(line_num+2, f"    mov rsi, {args_list[0].strip()}\n")
        out.insert(line_num+3, f"    mov rdx, {args_list[1].strip()}\n")
        out.insert(line_num+4, "    syscall\n")
        line_num += 5

    elif function_name == "begin_label":
        out.insert(line_num, f"{args_list[0].strip()}:\n")
        line_num += 1

    elif function_name == "global":
        out.insert(6 + bss_num+dat_num, out[5+dat_num+bss_num] + f"    global {args_list[0].strip()}\n")
        line_num += 1

    elif function_name == "call":
        out.insert(line_num, f"    call {args_list[0].strip()}\n")
        line_num += 1

    elif function_name == "return":
        try:
            out.insert(line_num, f"    ret {args_list[0]}\n")
        except IndexError:
            out.insert(line_num, "    ret\n")
        line_num += 1

    elif function_name == "syscall":
        args_list[0] = int(args_list[0].strip())
        if args_list[0] >= 0:
            out.insert(line_num, f"    mov rax, {args_list[1].strip()}\n")
        if args_list[0] >= 1:
            out.insert(line_num+1, f"    mov rdi, {args_list[2].strip()}\n")
        if args_list[0] >= 2:
            out.insert(line_num+2, f"    mov rsi, {args_list[3].strip()}\n")
        if args_list[0] >= 3:
            out.insert(line_num+3, f"    mov rdx, {args_list[4].strip()}\n")
        if args_list[0] >= 4:
            out.insert(line_num+4, f"    mov r10, {args_list[5].strip()}\n")
        if args_list[0] >= 5:
            out.insert(line_num+5, f"    mov r8, {args_list[6].strip()}\n")
        if args_list[0] == 6:
            out.insert(line_num+6, f"    mov r9, {args_list[7].strip()}\n")
        out.insert(line_num + args_list[0] + 1, "    syscall\n")
        line_num += args_list[0] + 2

#    out.insert(line_num, "    syscall\n")
#    line_num += 1

with open("out.asm", 'w') as file:
    file.writelines(out)

with open("out.asm", 'r') as file:
    print(file.read())

os.system("nasm -felf64 out.asm && ld out.o && rm out.asm out.o")

# subprocess.run(["nasm", "-felf64", "out.asm"])
# subprocess.run(["ld", "out.o"])
