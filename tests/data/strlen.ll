; ModuleID = 'strlen.c'
target datalayout = "e-p:32:32:32-i1:8:8-i8:8:8-i16:16:16-i32:32:32-i64:32:64-f32:32:32-f64:32:64-v64:64:64-v128:128:128-a0:0:64-f80:32:32-n8:16:32-S128"
target triple = "i386-pc-linux-gnu"

define i32 @_strlen(i8* nocapture %p) nounwind readonly {
  %1 = load i8* %p, align 1, !tbaa !0
  %2 = icmp eq i8 %1, 0
  br i1 %2, label %._crit_edge, label %.lr.ph

.lr.ph:                                           ; preds = %0, %.lr.ph
  %.02 = phi i8* [ %3, %.lr.ph ], [ %p, %0 ]
  %l.01 = phi i32 [ %4, %.lr.ph ], [ 0, %0 ]
  %3 = getelementptr inbounds i8* %.02, i32 1
  %4 = add i32 %l.01, 1
  %5 = load i8* %3, align 1, !tbaa !0
  %6 = icmp eq i8 %5, 0
  br i1 %6, label %._crit_edge, label %.lr.ph

._crit_edge:                                      ; preds = %.lr.ph, %0
  %l.0.lcssa = phi i32 [ 0, %0 ], [ %4, %.lr.ph ]
  ret i32 %l.0.lcssa
}

!0 = metadata !{metadata !"omnipotent char", metadata !1}
!1 = metadata !{metadata !"Simple C/C++ TBAA", null}
