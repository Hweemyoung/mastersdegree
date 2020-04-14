import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--q', help='Search term', default='Google')
    parser.add_argument('--max-results', help='Max results', default=50)
    args = parser.parse_args()
    print(args)