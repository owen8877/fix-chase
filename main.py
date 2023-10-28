import sys

from core import entrance

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    if len(sys.argv) < 2:
        error_msg = 'The file to be patched must be specified by the command line input!'
        print(error_msg)
        raise Exception(error_msg)

    account_id = input('Input the account id to be patched >')
    entrance(sys.argv[1], account_id)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
