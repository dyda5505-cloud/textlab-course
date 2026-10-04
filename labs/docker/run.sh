#!/usr/bin/env bash
set -euo pipefail
cd "$HOME"
touch "${STUDENT}.txt"
date +%A
ls -l /bin/bash
file /bin/bash
curl --fail --location --retry 3 http://www.lib.ru/CARROLL/alice.txt -o downloaded.txt
mv downloaded.txt alice.txt
wc -w < alice.txt
head -n 19 alice.txt
tail -n 17 alice.txt
mkdir -p test{1..40}
for number in {1..40}; do
    case "$number" in *3|*7) rmdir "test$number";; esac
done
printf '%s\n' test*/ | sort -V > test.txt
wc -l < test.txt
for number in {5..40..5}; do
    date +%F > "test$number/date.txt"
done
for number in {10..40..10}; do
    date +%T >> "test$number/date.txt"
done
test "$(wc -l < test.txt)" -eq 32
printf '\nCreated 32 directories; lab actions completed.\n'
