import sys
import os
import re

def split_ignore_quotes(args):
    pattern = re.compile(r'''((?:[^,"']|"[^"]*"|'[^']*')+)''')
    args_list = pattern.findall(args)
    args_list = [piece.strip('"\'') for piece in args_list]
    return args_list

out = []
aliases = {}
v_aliases = {}
dat_num = 0
bss_num = 0
txt_num = 0
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

with open(sys.argv[1], 'r') as file:
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
        args = args.strip()

        if args.endswith(")"):
            args = args[:-1].strip()
        else:
            print("Error: Malformed function call p2: " + str(line))
            sys.exit(1)
        args_list = split_ignore_quotes(args.strip())

    else:
        continue

    # todo: refactor if else chain to use match case
    if function_name == "comment": # make better comment system
        pass                       # this is stupid

    elif function_name == "use":
        with open(args_list[0], 'r') as using:
            using = pattern.findall(using.read())
            u_lines = [piece.strip('"\'') for piece in using]
            inc = 1
            for line in u_lines:
                inc += 1
                lines.insert(cur_pos + inc, line)

    elif function_name == "external":
        out.insert(6 + bss_num+dat_num, out[5+dat_num+bss_num] + f"    extern {args_list[0].strip()}\n")
        txt_num += 1
        line_num += 1

    elif function_name == "str_compare":
        # todo: remove the need for boilerplate asm in jumped functions
        out.insert(6 + bss_num+dat_num+txt_num, f"loop_{str(line_num)}:\n")
        out.insert(6 + bss_num+dat_num+txt_num+1, f"     mov al, [{args_list[0].strip()} + rdx]\n")
        out.insert(6 + bss_num+dat_num+txt_num+2, f"     mov bl, [{args_list[1].strip()} + rdx]\n")
        out.insert(6 + bss_num+dat_num+txt_num+3, "     inc rdx\n")
        out.insert(6 + bss_num+dat_num+txt_num+4, "     cmp al, bl\n")
        out.insert(6 + bss_num+dat_num+txt_num+5, f"     jne {args_list[3].strip()}\n")
        out.insert(6+ bss_num+dat_num+txt_num+6, "     cmp al, 0\n")
        out.insert(6 + bss_num+dat_num+txt_num+7, f"     je {args_list[2].strip()}\n")
        out.insert(6 + bss_num+dat_num+txt_num+8, f"     jmp loop_{str(line_num)}\n")

        out.insert(line_num+10, "    xor rdx, rdx\n")
        out.insert(line_num+11, f"    call loop_{str(line_num)}\n")
        line_num += 11

    elif function_name in aliases:
        increment = 0
        tmp = aliases[function_name]
        for arg in args_list:
            tmp = tmp.replace("%{arg"+str(increment)+"}", arg.strip())
            increment += 1
        out.insert(line_num, f"{tmp}\n")
        # out.insert(line_num, f"{aliases[function_name]}\n")
        line_num += 1

    elif function_name in v_aliases:
        tmp = v_aliases[function_name]

        args_amt = len(args_list)

        pos = tmp.splitlines()
        tincrement = 0
        for line in pos:
            if line.find("%rl{...}") != -1:
                break
            tincrement += 1
        increment = 0

        for arg in args_list:
            tmp = tmp.replace("%{arg"+str(increment)+"}", arg.strip())

            if args_list != None and "%{arg" not in tmp:
                pos[tincrement] = pos[tincrement].replace("%rl{...}", '')
                tmp = tmp.replace("%rl{...}", ', '.join(args_list).replace(', ', '\n'+pos[tincrement]))

            increment += 1
        increment = 0
        tmp2 = []
        for line in tmp.splitlines():
            if "%{arg" not in line and "%rl{...}" not in line:
                tmp2.append(line)

        tmp = '\n'.join(tmp2).replace("%{...}", args)
        out.insert(line_num, tmp+'\n')

        line_num += 1

    elif function_name == "alias":
        if args_list[0] == "variatic":
            v_aliases[args_list[1].strip()] = args_list[2].strip()[1:]
        else:
            aliases[args_list[0].strip()] = args_list[1].strip()[1:] # 1: for quote

    elif function_name == "raw_asm":
        out.insert(line_num, f"{args_list[0]}\n")
        line_num += 1

    elif function_name == "reserve":
        out.insert(2, f"    {args_list[2].strip()} {args_list[0].strip()} {args_list[1].strip()}\n")
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
            if split_res[increment] != "":
                split_res[increment] = f"    {args_list[0].strip()} \"{split_res[increment].strip()}\", 0x0\n"
            else:
                split_res[0] = split_res[0][:-1] + ", 0x0"
            args_list[2] = ''.join(split_res)
            out.insert(4+bss_num, f"   {args_list[1]}: {args_list[2]}\n")

        else:
            out.insert(4+bss_num, f"    {args_list[1].strip()}: {args_list[0].strip()} {args_list[2]}\", 0x0\n")
            args_list[2] = args_list[2] + '"'
        dat_num += 1
        line_num += 1

    elif function_name == "int_var":
        out.insert(4+bss_num, f"    {args_list[1].strip()} {args_list[0].strip()} {args_list[2]}\n")
        dat_num += 1
        line_num += 1

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

    elif function_name == "begin_label":
        out.insert(line_num, f"{args_list[0].strip()}:\n")
        line_num += 1

    elif function_name == "global":
        out.insert(6 + bss_num+dat_num, out[5+dat_num+bss_num] + f"    global {args_list[0].strip()}\n")
        txt_num +=1
        line_num += 1

    elif function_name == "call":
        out.insert(line_num, "    xor rax, rax\n")
        increment = 0

        for arg in args_list:
            if increment >= len(args_list) -1:
                break
            match increment:
                case 0:
                    out.insert(line_num+1, f"    mov rdi, {args_list[1]}\n")
                case 1:
                    out.insert(line_num+2, f"    mov rsi, {args_list[2]}\n")
                case 2:
                    out.insert(line_num+3, f"    mov rdx, {args_list[3]}\n")
                case 3:
                    out.insert(line_num+4, f"    mov rcx, {args_list[4]}\n")
                case 4:
                    out.insert(line_num+5, f"    mov r8, {args_list[5]}\n")
                case 5:
                    out.insert(line_num+6, f"    mov r9, {args_list[6]}\n")
                case increment if increment > 5 and increment < len(args_list) -1:
                    out.insert(line_num+increment+1, f"    push {args_list[increment+1]}\n")
            increment += 1
        out.insert(line_num+increment+2, "    mov rbp, rsp\n")
        out.insert(line_num+increment+3, "    and rsp, -16\n")
        out.insert(line_num+increment+4, f"    call {args_list[0].strip()}\n")
        out.insert(line_num+increment+5, "    mov rsp, rbp\n")

        line_num += 5+increment

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
print(''.join(out))

if '-linkc' in sys.argv:
    os.system("nasm -felf64 out.asm && gcc out.o -m64 -no-pie && rm out.asm out.o")
else:
    os.system("nasm -felf64 out.asm && ld out.o && rm out.asm out.o")

# subprocess.run(["nasm", "-felf64", "out.asm"])
# subprocess.run(["ld", "out.o"])
