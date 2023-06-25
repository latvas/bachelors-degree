import psutil
import subprocess
import csv
import os
import time
import datetime


def get_process_pid(name: str):
    command = list("ps -eo user,pid,args".split())
    ps_out = subprocess.run(command, capture_output=True, text=True)
    plist = list(ps_out.stdout.split("\n"))
    plist = list(map(lambda x: tuple(x.split()), plist))
    for elem in plist:
        if (len(elem) < 3):
            return None
        arg = elem[2]  # первый аргумент - это имя бинарника
        if name in arg:
            print(elem)
            return int(elem[1])  # elem[1] - PID
    return None


def __get_list_all_childs(inp_process: psutil.Process):
    processes = inp_process.children()

    for child in inp_process.children():
        tmp_pr = __get_list_all_childs(child)
        processes += tmp_pr

    return processes


def get_all_subprocesses(current_process: psutil.Process):
    processes = __get_list_all_childs(current_process)
    processes.insert(0, current_process)
    return processes


def remove_all_files_in_csv_dir():
    directory = 'csv/'

    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Directory created: {directory}")

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            os.remove(filepath)


def create_csv_files(processes: list()):
    csv_filenames = list(
        map(lambda x: ('csv/'+str(x.pid)+'_'+str(x.name())+'.csv', x), processes))
    header_row = tuple(
        "pid time cpu_user cpu_system total_cpu child_cpu_user child_cpu_system total_child_cpu cpu_percent thr_user_time thr_system_time rss_memory pss_memory memory_percent write read".split())

    csv_files = list()
    for filename, process in csv_filenames:
        if os.path.isfile(filename):
            csvfile = open(filename, 'a', newline='')
            writer = csv.writer(csvfile, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
        else:
            csvfile = open(filename, 'w', newline='')
            writer = csv.writer(csvfile, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(header_row)

        csv_files.append((csvfile, writer, process))

    return csv_files


def get_threads_cpu_time(process: psutil.Process):
    user_time = 0
    system_time = 0
    threads = process.threads()
    # print(process, threads)
    for thread in threads:
        user_time += thread.user_time
        system_time += thread.system_time
    return user_time, system_time


def get_process_info(process: psutil.Process):
    data = list()
    cpu_times = process.cpu_times()
    mem_info = process.memory_full_info()
    mem_percent = process.memory_percent()
    thr_user_time, thr_system_time = get_threads_cpu_time(process)
    num_read_bytes = process.io_counters().read_bytes
    num_write_bytes = process.io_counters().write_bytes
    data.append(process.pid)
    data.append(time.time())
    data.append(cpu_times.user)
    data.append(cpu_times.system)
    data.append(cpu_times.user + cpu_times.system)
    data.append(cpu_times.children_user)
    data.append(cpu_times.children_system)
    data.append(cpu_times.children_user + cpu_times.children_system)
    data.append(process.cpu_percent())
    data.append(thr_user_time)
    data.append(thr_system_time)
    data.append(mem_info.rss)
    data.append(mem_info.pss)
    data.append(mem_percent)
    data.append(num_write_bytes)
    data.append(num_read_bytes)
    return data


def main():
    name_string = "firefox"
    pid = get_process_pid(name_string)
    if pid is None:
        raise Exception(
            "process named '{}' does not exist".format(name_string))

    current_process = psutil.Process(pid)

    print(get_process_info(current_process))

    processes = get_all_subprocesses(current_process)

    remove_all_files_in_csv_dir()
    csv_files = create_csv_files(processes)
    # csv_files = create_csv_files([current_process])

    i = 0
    while (i < 10):
        for csvfile, writer, process in csv_files:
            data = get_process_info(process)
            now = datetime.datetime.now()
            time_str = now.strftime("%H:%M:%S")
            print(time_str, data)
            writer.writerow(data)
            pass
        time.sleep(2)
        i += 1

    '''
    with open('cpu_data.csv', 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow(map(lambda x: x.name, processes))
    '''


if __name__ == "__main__":
    main()
