# State-of-the-art planners to compare Kairos with, built from source at pinned commits:
#   docker build -t kairos/sota:benchmark bench/sota      (from planner_ws)
# Used by bench/coverage.py --planutils sota:NAME (run/NAME DOMAIN PROBLEM PLAN, time limit in
# $KAIROS_TIMEOUT seconds). Classical: IPC 2023 winners (Scorpion Maidu, Levitron, Fast
# Downward Stone Soup 2023, DecStar 2023) and Dual-BFWS; numeric: LNM-Plan (IPC 2023 winner,
# Numeric Fast Downward) and ENHSP; temporal and numeric: NextFLAP; lifted: Powerlifted.

# --- Fast Downward family (IPC 2023 classical) ------------------------------------------------
FROM ubuntu:22.04 AS fd
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git cmake g++ \
    make pypy3 python3 libboost-all-dev zlib1g-dev && rm -rf /var/lib/apt/lists/*
# Scorpion Maidu and Levitron (planner8)
RUN git clone https://github.com/ipc2023-classical/planner8 /p/maidu && cd /p/maidu && \
    git checkout cb89061 && rm -rf builds && pypy3 build.py -j8 && \
    strip --strip-all builds/release/bin/* || true
RUN cd /p/maidu/ext/powerlifted && pypy3 build.py && \
    strip --strip-all builds/release/search/search || true
RUN cd /p/maidu/ext/cpddl && make && make -C bin || true
# Fast Downward Stone Soup 2023 (planner28)
RUN git clone https://github.com/ipc2023-classical/planner28 /p/fdss && cd /p/fdss && \
    git checkout c2f1e05 && rm -rf builds && pypy3 build.py -j8 && \
    strip --strip-all builds/release/bin/downward
# DecStar 2023 (planner15), without CPLEX (its satisficing and agile configurations use no LP)
RUN git clone https://github.com/ipc2023-classical/planner15 /p/decstar && cd /p/decstar && \
    git checkout be47954 && cd third-party/bliss-0.73 && make clean && make && make lib && \
    cd /p/decstar && rm -rf builds && PATH=/p/decstar/third-party/bliss-0.73:$PATH \
    pypy3 build.py release64 -j8 && strip --strip-all builds/release64/bin/* || true

# --- LNM-Plan (IPC 2023 numeric winner, Numeric Fast Downward), without LP (its LP code needs CPLEX; the satisficing configurations use none) ---------------------------------
FROM ubuntu:22.04 AS lnm
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git cmake g++ \
    make python2 python3 zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/ipc2023-numeric/team-1 /p/lnm && cd /p/lnm && \
    git checkout 6f521a9 && cd src/search/bliss-0.73 && make && cd /p/lnm && \
    python3 build.py release64 -j8

# --- Dual-BFWS (LAPKT of 2020: later ones moved the FF parser that BFWS builds on) -------------------------------------------------------------------------
FROM ubuntu:22.04 AS bfws
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends build-essential ca-certificates \
    xutils-dev scons flex bison libboost-dev libjudy-dev libboost-python-dev \
    libboost-program-options-dev g++ git python3 && rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/LAPKT-dev/LAPKT-public.git /p/LAPKT-public && \
    cd /p/LAPKT-public && git checkout 99b68f5 && \
    git clone https://github.com/nirlipo/BFWS-public.git /p/BFWS && cd /p/BFWS && \
    git checkout d241392 && cd /p/LAPKT-public/external/libff && make clean && make depend && \
    make ADDONS=-fcommon && cd /p/BFWS/ff-version && LAPKT_PATH=/p/LAPKT-public scons -j8

# --- ENHSP -------------------------------------------------------------------------------------
FROM ubuntu:22.04 AS enhsp
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git \
    openjdk-17-jdk-headless && rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/hstairs/enhsp /p/enhsp && cd /p/enhsp && git checkout bb0415c && \
    ./compile

# --- NextFLAP ----------------------------------------------------------------------------------
FROM ubuntu:22.04 AS nextflap
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git g++ make \
    libz3-dev && rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/ossaver/NextFLAP /p/nextflap && cd /p/nextflap && \
    git checkout dc9cb46 && mkdir -p z3/include z3/lib && \
    cp /usr/include/z3*.h z3/include/ && ln -sf /usr/lib/x86_64-linux-gnu/libz3.so z3/lib/libz3.so && \
    make -j8

# --- Powerlifted (lifted classical planning, Correa et al.) --------------------------------------
FROM ubuntu:22.04 AS powerlifted
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git cmake g++ \
    make python3 python3-dev && rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/abcorrea/powerlifted /p/powerlifted && cd /p/powerlifted && \
    git checkout bf54e16 && rm -rf builds && python3 build.py && \
    strip --strip-all builds/release/search/search

# --- Runtime -----------------------------------------------------------------------------------
FROM ubuntu:22.04
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends pypy3 python2 python3 \
    openjdk-17-jre-headless libz3-4 libjudy-dev libboost-program-options1.74.0 \
    time && rm -rf /var/lib/apt/lists/*
COPY --from=fd /p/maidu /p/maidu
COPY --from=fd /p/fdss/driver /p/fdss/driver
COPY --from=fd /p/fdss/fast-downward.py /p/fdss/
COPY --from=fd /p/fdss/builds/release/bin /p/fdss/builds/release/bin
COPY --from=fd /p/decstar /p/decstar
COPY --from=lnm /p/lnm /p/lnm
COPY --from=bfws /p/BFWS/ff-version/bfws /p/bfws/bfws
COPY --from=enhsp /p/enhsp/enhsp-dist /p/enhsp
COPY --from=nextflap /p/nextflap/nextflap /p/nextflap/nextflap
COPY --from=powerlifted /p/powerlifted /p/powerlifted
COPY run /run-planner
RUN chmod +x /run-planner/*
