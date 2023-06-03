#!/usr/bin/env python3

import sys

'''
This script finds the most common two-character sequences
and replace them with a single uppercase character or
special character, to compression purposes.
'''

if len(sys.argv) != 4:
    print("{}: <host list.txt> <awk output.awk> <pac function.js>".format(sys.argv[0]))
    sys.exit(1)

patternhit = {}
# "&" character should be prepended with two backslashes for awk's gsub.
wordreplace=["A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
             "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
             "U", "V", "W", "X", "Y", "Z",
             "!", "@", "#", "$", "%", "^", "\\\\&", "*", "(", ")",
             "=", "+", "/", ",", "<", ">", "~", "[", "]", "{", "}"]

with open(sys.argv[1], "r") as dfile:
    domains = dfile.read().split("\n")

    new_domains = []
    for domain in domains:
        new_domains.append('.'.join(domain.split(".")[:-1]))
    domains = ''.join(new_domains)

    domain_len = len(domains)
    position = 0

    while position <= domain_len:
        cut = domains[position:position+2]
        if not patternhit.get(cut):
            patternhit[cut] = 0
        patternhit[cut] += 1
        position += 2

patternhit = dict(sorted(patternhit.items(), key=lambda x: x[1]))

#print(patternhit, file=sys.stderr)
finallist = list(patternhit)[-1 * len(wordreplace):]
#print(finallist, file=sys.stderr)

with open(sys.argv[2], "w") as awkfile:
    print("{", file=awkfile)
    for i, w in enumerate(finallist):
        print('gsub(/{}/, "{}", domainname)'.format(w, wordreplace[i]), file=awkfile)
    print("}", file=awkfile)

with open(sys.argv[3], "w") as pacfile:
    pacdict = {}
    for i, w in enumerate(finallist):
        pacdict[wordreplace[i].strip('\\')] = w
    print(pacdict, file=pacfile)
