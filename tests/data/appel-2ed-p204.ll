define i32 @func(i32 %c, i32 %N) {
entry:
  %a = mov i32 0

L1:
  %b = add i32 %a, 1
  %c = add i32 %c, %b
  %a = mul i32 %b, 2
  %btmp = icmp lt i32 %a, %N
  br i1 %btmp, label %L1, label %b2

b2:
  ret i32 %c
}
