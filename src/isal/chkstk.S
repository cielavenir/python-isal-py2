// https://github.com/llvm-mirror/compiler-rt/blob/master/lib/builtins/i386/chkstk.S
// https://github.com/llvm-mirror/compiler-rt/blob/master/lib/builtins/x86_64/chkstk.S

// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception

// _chkstk routine
// This routine is windows specific
// http://msdn.microsoft.com/en-us/library/ms648426.aspx

// Notes from r227519
// MSVC x64s __chkstk and cygmings ___chkstk_ms do not adjust %rsp
// themselves. It also does not clobber %rax so we can reuse it when
// adjusting %rsp.

.global ___chkstk_ms
.text
.balign 4

___chkstk_ms:
#if defined(__x86_64__)
        push   %rcx
        push   %rax
        cmp    $0x1000,%rax
        lea    24(%rsp),%rcx
        jb     1f
2:
        sub    $0x1000,%rcx
        test   %rcx,(%rcx)
        sub    $0x1000,%rax
        cmp    $0x1000,%rax
        ja     2b
1:
        sub    %rax,%rcx
        test   %rcx,(%rcx)
        pop    %rax
        pop    %rcx
        ret
#elif defined(__i386__)
        push   %ecx
        push   %eax
        cmp    $0x1000,%eax
        lea    12(%esp),%ecx
        jb     1f
2:
        sub    $0x1000,%ecx
        test   %ecx,(%ecx)
        sub    $0x1000,%eax
        cmp    $0x1000,%eax
        ja     2b
1:
        sub    %eax,%ecx
        test   %ecx,(%ecx)
        pop    %eax
        pop    %ecx
        ret
#endif
