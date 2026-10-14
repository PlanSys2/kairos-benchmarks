#!/usr/bin/env python3
# Copyright 2026 Intelligent Robotics Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Gets the third-party problems of the suites, exactly as they were measured.

  fetch.py [--dir DIR] [SUITE...]     download the files the suites name (default: all), at
                                      the commits of sources.tsv, and check their sha256
  fetch.py --list [--dir DIR] SUITE   print "label domain problem" with absolute paths

Only the files the suites use are checked out (git sparse checkout), into DIR (default
~/.cache/kairos-benchmarks). The problems of this repository (generated/) need nothing.
"""

import argparse
import collections
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def sources():
    out = {}
    with open(os.path.join(HERE, 'sources.tsv')) as fh:
        for line in fh:
            if line.strip() and not line.startswith('#'):
                name, url, commit = line.rstrip('\n').split('\t')
                out[name] = (url, commit)
    return out


def suite(name):
    rows = []
    with open(os.path.join(HERE, 'suites', name + '.tsv')) as fh:
        for line in fh:
            if line.strip() and not line.startswith('#'):
                rows.append(line.rstrip('\n').split('\t'))
    return rows


def all_suites():
    return sorted(f[:-4] for f in os.listdir(os.path.join(HERE, 'suites')) if f.endswith('.tsv'))


def path_of(base, source, rel):
    if source == 'kairos-benchmarks':
        return os.path.join(HERE, rel)
    return os.path.join(base, source, rel)


def git(*args, cwd=None):
    subprocess.run(['git'] + list(args), cwd=cwd, check=True, stdout=subprocess.DEVNULL)


def fetch(base, names):
    srcs = sources()
    wanted = collections.defaultdict(set)
    expected = {}
    for name in names:
        for label, source, domain, problem, dsha, psha in suite(name):
            for rel, sha in ((domain, dsha), (problem, psha)):
                expected[(source, rel)] = sha
                if source != 'kairos-benchmarks':
                    wanted[source].add(rel)
    for source, files in sorted(wanted.items()):
        url, commit = srcs[source]
        folder = os.path.join(base, source)
        if not os.path.isdir(os.path.join(folder, '.git')):
            os.makedirs(folder, exist_ok=True)
            git('init', '-q', cwd=folder)
            git('remote', 'add', 'origin', url, cwd=folder)
            git('config', 'core.sparseCheckout', 'true', cwd=folder)
        # Sparse checkout of exactly these files (added to those of earlier calls)
        info = os.path.join(folder, '.git', 'info', 'sparse-checkout')
        old = set(open(info).read().split('\n')) if os.path.exists(info) else set()
        with open(info, 'w') as fh:
            fh.write('\n'.join(sorted((old | {'/' + f for f in files}) - {''})) + '\n')
        git('fetch', '-q', '--depth', '1', '--filter=blob:none', 'origin', commit, cwd=folder)
        git('checkout', '-q', commit, cwd=folder)
        print('%-28s %s  %d files' % (source, commit[:12], len(files)))
    bad = 0
    for (source, rel), sha in sorted(expected.items()):
        path = path_of(base, source, rel)
        try:
            with open(path, 'rb') as fh:
                ok = hashlib.sha256(fh.read()).hexdigest() == sha
        except OSError:
            ok = False
        if not ok:
            bad += 1
            print('MISMATCH %s: %s' % (source, rel), file=sys.stderr)
    print('%d files checked, %d mismatches' % (len(expected), bad))
    return bad == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('suites', nargs='*')
    ap.add_argument('--dir', default=os.path.expanduser('~/.cache/kairos-benchmarks'))
    ap.add_argument('--list', action='store_true')
    args = ap.parse_args()
    names = args.suites or all_suites()
    if args.list:
        for name in names:
            for label, source, domain, problem, _d, _p in suite(name):
                print(label, path_of(args.dir, source, domain), path_of(args.dir, source, problem))
        return 0
    return 0 if fetch(args.dir, names) else 1


if __name__ == '__main__':
    sys.exit(main())
