ADOT2DOT = ../../adot2dot
CLANG2LLVM = ../../clang2llvm

%.dot: %.adot
	$(ADOT2DOT) $< $@

%.ll: %.c
	$(CLANG2LLVM) $< -o $@

all: \
    appel-2ed-p221.dot \
    strlen.ll

appel-2ed-p221.dot: appel-2ed-p221.adot

strlen.ll: strlen.c
