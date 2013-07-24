
@g = common global i32 0

define i32 @func(i32 %k, i32 %j) {
entry:
  %g = load getelementptr i32* %j, i32 10
  %h = sub i32 %k, 1
  %f = mul i32 %g, %h
  %e = load getelementptr i32* %j, i32 8
  %m = load getelementptr i32* %j, i32 16
  %b = load i32* %f
  %c = add i32 %e, 8
  %d = mov i32 %c
  %k = add i32 %m, 4
  %j = mov i32 %b
  store i32 %d, i32* @g_d
  store i32 %k, i32* @g_k
  store i32 %j, i32* @g_j
  ret i32 0
}
