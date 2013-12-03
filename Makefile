BASEDIRS = hpss

######################################################################
# Configuration should occur above this line


GCC = g++ 

ifeq ($(EIRODS_BUILD_COVERAGE), 1)
GCC += -fprofile-arcs -ftest-coverage -lgcov
endif

export OBJDIR = .objs
export DEPDIR = .deps
export SOTOPDIR = .

SUBS = ${BASEDIRS}

.PHONY: ${SUBS} clean

default: ${SUBS}

${SUBS}:
	@-mkdir -p $@/${OBJDIR} > /dev/null 2>&1
	@-mkdir -p $@/${DEPDIR} > /dev/null 2>&1
	${MAKE} -C $@

clean:
	@-for dir in ${SUBS}; do \
	echo "Cleaning $$dir"; \
	rm -f $$dir/${OBJDIR}/*.o > /dev/null 2>&1; \
        rm -f $$dir/${DEPDIR}/*.d > /dev/null 2>&1; \
	rm -f $$dir/*.o > /dev/null 2>&1; \
	done
	@-rm -f ${SOTOPDIR}/*.so > /dev/null 2>&1

