# coding=utf-8

"""
Watchdog for danila-mainer (Ton Mining Pool)

Usage:

Windows:
    py danila_miner_watchdog.py danila-miner.exe run https://pool.services.tonwhales.com YOUR_WALLET

Linux:
    python3 danila_miner_watchdog.py ./danila-miner run https://pool.services.tonwhales.com YOUR_WALLET
"""

import subprocess
import argparse
import time
import sys
import signal

IS_WIN32 = sys.platform == 'win32'

if IS_WIN32:
    import console_ctrl


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('command', nargs='+', help='Miner command executable and its arguments')
    return p.parse_args()


def run_command(command):

    kwargs = {}

    if IS_WIN32:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags = subprocess.CREATE_NEW_CONSOLE | subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        kwargs['startupinfo'] = startupinfo
        kwargs['creationflags'] = subprocess.CREATE_NEW_CONSOLE

    return subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **kwargs,
    )


def close_proc(proc):
    if IS_WIN32:
        console_ctrl.send_ctrl_c(proc.pid)
    else:
        proc.send_signal(signal.SIGINT)
    proc.wait()


RESTART_INTERVAL = 5


def main():
    args = parse_args()

    # signal.signal(signal.SIGINT, quit_handler)

    print('Starting pool miner... Press Ctrl+C to quit.')

    proc = run_command(args.command)

    try:
        while True:
            while True:
                stderr_line = proc.stderr.readline()
                if not stderr_line:
                    stdout_line = proc.stdout.readline()
                else:
                    stdout_line = b''

                try:
                    stdout_line = stdout_line.strip().decode()
                    stderr_line = stderr_line.strip().decode()
                except UnicodeDecodeError:
                    continue

                # Show log
                print(stderr_line)

                # Check log for errors
                if 'error' in stdout_line or 'Error:' in stderr_line:
                    if stdout_line:
                        print(f'ERROR: {stdout_line}')
                    break

                if 'hashrate 0.0' in stderr_line:
                    print('Something went wrong! hashrate is 0.00')
                    break

            print(f'An error occurred! Restarting in {RESTART_INTERVAL} seconds...')
            close_proc(proc)
            time.sleep(RESTART_INTERVAL)

            proc = run_command(args.command)

    except KeyboardInterrupt:
        print('Exiting')
        close_proc(proc)


if __name__ == '__main__':
    main()
