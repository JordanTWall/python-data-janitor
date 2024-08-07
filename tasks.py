from invoke import task
from pymongo import MongoClient
from modules import get_database, get_mongo_client
from functions.mongo_data_scrubber import mongo_data_scrubber

def parse_years(years_arg):
    if years_arg == "all":
        return "all"
    years = set()
    try:
        for part in years_arg.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                years.update(range(start, end + 1))
            else:
                years.add(int(part))
        return sorted(years)
    except ValueError:
        raise ValueError("Years must be a comma-separated list of integers or ranges in 'YYYY-YYYY' format.")

@task
def mongo_scrub(c, teams="all", years="all"):
    """Run the MongoDB data scrubber for specified teams and years."""
    client = get_mongo_client()
    db = get_database(client)
    if years != "all":
        years = parse_years(years)
    mongo_data_scrubber(db, years, teams)
    client.close()

@task
def check(ctx, team='all', years='all'):
    ctx.run(f"python main.py check --team {team} --years {years}")

@task
def check_all(ctx):
    ctx.run(f"python main.py check --team all --years all")

@task
def download(ctx, years='all'):
    ctx.run(f"python main.py download --years {years}")

@task
def download_all(ctx):
    ctx.run(f"python main.py download --years all")

@task
def download_preseason(ctx, years='all'):
    ctx.run(f"python main.py download_preseason --years {years}")

@task
def download_preseason_all(ctx):
    ctx.run(f"python main.py download_preseason --years all")

@task
def scrub(ctx):
    ctx.run("python main.py scrub")
