import subprocess as sb

from globals import ERROR_MESSAGE


def run_cmd(cmd: list[str]):
    """Execute a command in the operational system

    Args:
        cmd (list[str]): the application to be executed and its arguments
    """
    try:
        process = sb.Popen(" ".join(cmd), shell=True, stdout=sb.PIPE,
                           stderr=sb.PIPE)
        stdout, stderr = process.communicate()
        process_output = clean_output(stdout.strip())
        process_error = clean_output(stderr.strip())

        if len(process_output) > 1:
            print('subprocess result: ', process_output)
        else:
            print('subprocess error: ', process_error)

        return stdout
    except Exception as err:
        print(ERROR_MESSAGE, err)


def clean_output(output):
    output = str(output).replace('b', '').replace("'", '')
    return output
