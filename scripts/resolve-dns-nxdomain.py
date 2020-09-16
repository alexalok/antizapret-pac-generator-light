#!/usr/bin/env python3

import sys
import os
import asyncio
import dns.resolver
import dns.asyncresolver
import dns.exception
import dns._asyncio_backend

# DNS timeout (in seconds) for the initial DNS resolving pass
INITIAL_PASS_TIMEOUT = 3
# Number of concurrent resolving 'threads' for initial pass
INITIAL_PASS_CONCURRENCY = 100

# DNS timeout (in seconds) for the final (second) DNS resolving pass
FINAL_PASS_TIMEOUT = 10
# Number of concurrent resolving 'threads' for final pass
FINAL_PASS_CONCURRENCY = 35


class AZResolver(dns.asyncresolver.Resolver):
    def __init__(self, *args, **kwargs):
        self.limitConcurrency(25) # default limit
        super().__init__(*args, **kwargs)

    def limitConcurrency(self, count):
        self.limitingsemaphore = asyncio.Semaphore(count)

    async def nxresolve(self, domain):
        async with self.limitingsemaphore:
            try:
                #print(domain, file=sys.stderr)
                await self.resolve(domain)

            except (dns.exception.Timeout, dns.resolver.NXDOMAIN,
                    dns.resolver.YXDOMAIN, dns.resolver.NoNameservers):
                return domain
            except dns.resolver.NoAnswer:
                # Do not thread domain as broken if the answer is empty
                pass

async def runTasksWithProgress(tasks):
    progress = 0
    old_progress = 0
    ret = []

    for task in asyncio.as_completed(tasks):
        ret.append(await task)
        progress = int(len(ret) / len(tasks) * 100)
        if old_progress < progress:
            print("{}%...".format(progress), end='\r', file=sys.stderr, flush=True)
            old_progress = progress
    print(file=sys.stderr)
    return ret

async def main():
    if len(sys.argv) != 2:
        print("Incorrect arguments!")
        sys.exit(1)

    r = AZResolver()
    r.limitConcurrency(INITIAL_PASS_CONCURRENCY)
    r.timeout = INITIAL_PASS_TIMEOUT
    r.lifetime = INITIAL_PASS_TIMEOUT

    # Load domain file list and schedule resolving
    tasks = []
    try:
        with open(sys.argv[1], 'rb') as domainlist:
            for domain in domainlist:
                tasks.append(asyncio.ensure_future(r.nxresolve(domain.decode().strip())))
    except OSError as e:
        print("Can't open file", sys.argv[1], e, file=sys.stderr)
        sys.exit(2)

    print("Loaded list of {} elements, resolving NXDOMAINS".format(len(tasks)), file=sys.stderr)
    #sys.exit(0)

    try:
        # Resolve domains, first try
        nxresolved_first = await runTasksWithProgress(tasks)
        nxresolved_first = list(filter(None, nxresolved_first))

        print("Got {} broken domains, trying to resolve them again "
              "to make sure".format(len(nxresolved_first)), file=sys.stderr)

        # Second try
        tasks = []
        r.limitConcurrency(FINAL_PASS_CONCURRENCY)
        r.timeout = FINAL_PASS_TIMEOUT
        r.lifetime = FINAL_PASS_TIMEOUT

        for domain in nxresolved_first:
            tasks.append(asyncio.ensure_future(r.nxresolve(domain)))
        nxresolved_second = await runTasksWithProgress(tasks)
        nxresolved_second = list(filter(None, nxresolved_second))

        print("Finally, got {} broken domains".format(len(nxresolved_second)), file=sys.stderr)
        for domain in nxresolved_second:
            print(domain)

    except (SystemExit, KeyboardInterrupt):
        for task in tasks:
            task.cancel()


if __name__ == '__main__':
    if dns.__version__ == '2.0.0':
        # Monkey-patch dnspython 2.0.0 bug #572
        # https://github.com/rthalley/dnspython/issues/572
        class monkeypatched_DatagramProtocol(dns._asyncio_backend._DatagramProtocol):
                def error_received(self, exc):  # pragma: no cover
                    if self.recvfrom and not self.recvfrom.done():
                        self.recvfrom.set_exception(exc)

                def connection_lost(self, exc):
                    if self.recvfrom and not self.recvfrom.done():
                        self.recvfrom.set_exception(exc)

        dns._asyncio_backend._DatagramProtocol = monkeypatched_DatagramProtocol

    try:
        asyncio.run(main())
    except (SystemExit, KeyboardInterrupt):
        sys.exit(3)
