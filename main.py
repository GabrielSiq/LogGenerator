import argparse
import config
from datetime import datetime, timedelta
from simulation_manager import SimulationManager


def parse_args():
    today = datetime.now().date()
    parser = argparse.ArgumentParser(description='LogGenerator — business process simulator')
    parser.add_argument('--input', default='input', help='Input directory containing XML files and rules/data modules (default: input/)')
    parser.add_argument('--start', default=str(today - timedelta(days=7)), help='Simulation start date YYYY-MM-DD (default: 7 days ago)')
    parser.add_argument('--end', default=str(today), help='Simulation end date YYYY-MM-DD (default: today)')
    parser.add_argument('--name', default=None, help='Output filename without extension (default: auto timestamp)')
    parser.add_argument('--output', default='output/', help='Output directory (default: output/)')
    parser.add_argument('--resource-limit', nargs='*', metavar='KEY=VALUE', help='Override resource quantities e.g. support=20 trust=5')
    return parser.parse_args()


def main():
    args = parse_args()

    start = datetime.strptime(args.start, '%Y-%m-%d')
    end = datetime.strptime(args.end, '%Y-%m-%d').replace(hour=23, minute=59)

    resource_limit = None
    if args.resource_limit:
        resource_limit = dict(kv.split('=', 1) for kv in args.resource_limit)

    input_dir = args.input.rstrip('/')
    config.DEFAULT_PATHS['activities'] = f'{input_dir}/activities.xml'
    config.DEFAULT_PATHS['resources'] = f'{input_dir}/resources.xml'
    config.DEFAULT_PATHS['data'] = f'{input_dir}/data.xml'
    config.DEFAULT_PATHS['models'] = f'{input_dir}/models.xml'
    config.DEFAULT_PATHS['log'] = args.output
    config.DEFAULT_PATHS['rules_function'] = f'{input_dir.replace("/", ".")}.rules'
    config.DEFAULT_PATHS['data_function'] = f'{input_dir.replace("/", ".")}.data'

    sm = SimulationManager(start=start, end=end)
    sm.simulate(name=args.name, resource_limit=resource_limit)


if __name__ == '__main__':
    main()
