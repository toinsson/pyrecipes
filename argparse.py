desc = ''
parser = argparse.ArgumentParser(description=desc)

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-s', action='store_const', const = 1, help='switch action 1')
group.add_argument('-c', action='store_const', const = 2, help='switch action 2')
group.add_argument('-o', action='store_const', const = 3, help='switch action 3')

parser.add_argument('--dir', '-d', metavar='path', help='path to the data', required=True)
parser.add_argument('--name', '-n', metavar='file', help='name for file', required=True)

args = parser.parse_args()

options = args.s or args.c or args.o
funcs = {1 : func1,
         2 : func2,
         3 : func3}

funcs[options](args.dir, args.name)