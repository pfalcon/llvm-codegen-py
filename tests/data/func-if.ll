@b = common global i32 0
@c = common global i32 0
@a = common global i32 0

declare i32 @foo()

declare i32 @bar()

define i32 @baz(i32 %x) {
entry:
  %ifcond = icmp eq i32 %x, 1
  br i1 %ifcond, label %then, label %else

then:
  %0 = load i32* @b
  %1 = load i32* @c
  %tmp = add i32 %1, %0
  br label %ifcont

else:
  %2 = load i32* @b
  %3 = load i32* @c
  %tmp1 = sub i32 %2, %3
  br label %ifcont

ifcont:
  %iftmp = phi i32 [ %tmp, %then ], [ %tmp1, %else ]
  store i32 %iftmp, i32* @a
  ret i32 %iftmp
}
