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
line_num = 0
out.insert(line_num, "SECTION .data\n")
out.insert(line_num+1, "") # data section to avoid problems with list comprehension
out.insert(line_num+2, "SECTION .text\n")
out.insert(line_num+3, "    global _start\n")
out.insert(line_num+4, "_start:\n")
line_num += 5

file = open(sys.argv[1], 'r')
file = file.read()

lines = file.splitlines()

for line in lines:
    line = line.strip()
    if line:
        if "(" not in line or ")" not in line:
            print("Error: Malformed function call: " + str(line))
            sys.exit(1)

        function_name, args = line.split("(", 1)
        if args.endswith(")"):
            args = args[:-1]
        else:
            print("Error: Malformed function call: " + str(line))
            sys.exit(1)
        args_list = split_ignore_quotes(args)
    else:
        continue

    if function_name == "strconst":
        if '\\n' in args_list[1]:
            args_list[1] = args_list[1].replace('\\n', "\", 10, \"")
            if args_list[1].endswith('""'):
                args_list[1] = args_list[1][:-4]
            elif args_list[1].endswith('"'):
                args_list[1] = args_list[1][:-3]
            # temp = args_list[1].split('\\n')
            # args_list[1] = temp[0] + '"' + ', 13, 10, ' + '"' + temp[1]
        out.insert(2, out[1] + f"    {args_list[0].strip()} db {args_list[1]}, 0x0\n")
        line_num += 1

    elif function_name == "exit":
        out.insert(line_num, "    mov rax, 60\n")
        out.insert(line_num+1, f"    mov rdi, {args_list[0].strip()}\n")
        out.insert(line_num+2, "    syscall\n")
        line_num += 3

    elif function_name == "write":
        out.insert(line_num, "    mov rax, 1\n")
        out.insert(line_num+1, "    mov rdi, 1\n")
        out.insert(line_num+2, f"    mov rsi, {args_list[0].strip()}\n")
        out.insert(line_num+3, f"    mov rdx, {args_list[1].strip()}\n")
        out.insert(line_num+4, "    syscall\n")
        line_num += 5


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
