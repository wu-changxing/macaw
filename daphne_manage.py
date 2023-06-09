import sys

if __name__ == '__main__':
    # insert here whatever commands you use to run daphne
    sys.argv = ['daphne','mysite.asgi:application', '-b', '127.0.0.1', '-p', '8888', ]
    from daphne.cli import CommandLineInterface

    CommandLineInterface.entrypoint()
