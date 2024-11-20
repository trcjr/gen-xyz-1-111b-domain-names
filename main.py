
import logging
import asyncio
from async_dns.core import types, Address
from async_dns.resolver import DNSClient

BLOCK_SIZE =    1_100_000
UPPER_LIMIT = 999_999_999
CHECKPOINT_FILE = "checkpoint.txt"
NAME_SERVER = "192.168.50.3"

log = logging.getLogger(__name__)
logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        filename='main.log',
        #level=logging.DEBUG
        level=logging.INFO
        )

ASYNC_SEMAPHORE = asyncio.Semaphore(500)

def is_prime(n):
    n = int(n)
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

def is_palindrome(num):
    num = str(num)
    return num == num[::-1]

def has_unique_characters(i):
    data = {}
    for c in str(i):
        data[c] = data.get(c, 0) + 1
    for (k, v) in data.items():
        if v > 1:
            return False
    return True

async def has_soa_record(domain):
    async with ASYNC_SEMAPHORE:
        try:
            client = DNSClient()
            res = await client.query(domain, types.SOA, Address.parse(NAME_SERVER))
            log.debug(res)
            if len(res.an):
                log.debug(f"{domain} - {res.an[0].data}")
                return True
            return False
        except Exception:
            return False

async def check_number(i):
        if i % 50_000 == 0:
            write_last_number(i)
            log.critical(f"checkpoint: {i}")

        z = str(i).zfill(6)

        if i % 500_000 == 0:
            p = (i / UPPER_LIMIT ) * 100
            log.warning(f"PROGRESS UPDATE - i: {z} / {UPPER_LIMIT} -- {p:.05f} - {len(z)}");

        domain = z + ".xyz"
        if is_prime(z) and has_unique_characters(z):
            if not await has_soa_record(domain):
                log.info(f"PGD: {domain}")
                return True
        return False

def write_last_number(i):
    with open(CHECKPOINT_FILE, "w") as f:
        f.write(str(i))

def read_last_number():
    with open(CHECKPOINT_FILE, "r") as f:
        return int(f.read())

async def main():

    # Try to resume
    try:
        lower = read_last_number()
    except:
        lower = 1

    while lower < UPPER_LIMIT:
        tasks = set()
        for i in range(lower, lower + BLOCK_SIZE):

            task = asyncio.create_task( check_number(i) )
            task.add_done_callback(tasks.discard)
            tasks.add(task)
        if len(tasks):
            await asyncio.wait(tasks)
        lower = lower + BLOCK_SIZE

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())